import { TextField } from "@web/views/fields/text/text_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

patch(TextField.prototype, {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.toggleRecording = this.toggleRecording.bind(this); // Bind toggleRecording
        this.appendTextToField = this.appendTextToField.bind(this);
    },

    async toggleRecording() {
        if (this.isRecording) {
            // Stop recording
            this.isRecording = false;
            this.mediaRecorder.stop();
            this.notification.add("Recording stopped.", {
                title: "Recording",
                type: "info",
                sticky: false,
            });
        } else {
            // Start recording
            this.isRecording = true;
            this.audioChunks = [];

            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(stream);

                this.mediaRecorder.ondataavailable = (event) => {
                    this.audioChunks.push(event.data);
                };

                this.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    const audioBase64 = await this.blobToBase64(audioBlob);

                    this.notification.add("Processing transcription...", {
                        title: "Processing",
                        type: "info",
                        sticky: false,
                    });

                    rpc("/voice_to_text/recognize", { audio_data: audioBase64 })
                        .then((response) => {
                            if (response.status === "success") {
                                this.notification.add("Transcription completed.", {
                                    title: "Success",
                                    type: "success",
                                });
                                this.appendTextToField(response.text);
                            } else {
                                this.notification.add(response.message || "Failed to transcribe audio.", {
                                    title: "Error",
                                    type: "danger",
                                });
                            }
                            this.env.searchModel._notify();
                        })
                        .catch((error) => {
                            console.error("Error during transcription RPC:", error);
                            this.notification.add("Failed to transcribe audio.", {
                                title: "Error",
                                type: "danger",
                            });
                        });
                };

                this.mediaRecorder.start();

                this.notification.add("Recording started. Please start speaking...", {
                    title: "Recording",
                    type: "info",
                    sticky: false,
                });
            } catch (error) {
                console.error("Error accessing microphone:", error);

                this.notification.add("Error accessing microphone.", {
                    title: "Error",
                    type: "danger",
                });
                this.isRecording = false;
            }
        }

        // Update button style dynamically
        this.updateButtonStyle();
    },

    updateButtonStyle() {
        const button = document.querySelector("#record_voice");
        if (this.isRecording) {
            button.classList.add("recording");
        } else {
            button.classList.remove("recording");
        }
    },

    async blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result.split(",")[1]);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    },

    appendTextToField(transcription) {
        const field = this.props.name;
        const model = this.props.record.resModel;
        const id = this.props.record.resId;

        if (!transcription.trim()) {
            this.notification.add("No transcription available to save.", {
                title: "Error",
                type: "warning",
            });
            return;
        }

        rpc("/voice_to_text/update_field", {
            field: field,
            model: model,
            script: transcription,
            record_id: id,
        })
            .then((response) => {
                this.notification.add(response.message || "Text added successfully!", {
                    title: "Success",
                    type: "success",
                });
                this.env.searchModel._notify();
            })
            .catch((error) => {
                console.error("Error during field update RPC:", error);
                this.notification.add("Failed to save text to the field.", {
                    title: "Error",
                    type: "danger",
                });
            });
    },
});
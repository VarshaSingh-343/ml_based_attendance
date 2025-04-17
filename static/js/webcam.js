const startBtn = document.getElementById('start-button');
const webcamContainer = document.getElementById('webcam-container');
const video = document.getElementById('video');
const statusText = document.getElementById('status');

startBtn.addEventListener('click', () => {
    webcamContainer.style.display = 'block';

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        });

    setInterval(() => {
        let canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        let context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        let dataURL = canvas.toDataURL('image/jpeg');

        fetch('/process_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: dataURL })
        })
        .then(res => res.json())
        .then(data => {
            statusText.textContent = data.message;
        });
    }, 2000); // every 2 seconds
});

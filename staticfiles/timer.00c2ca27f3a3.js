// timer.js

function updateDetailTimer() {
    var endTime = Date.parse("{{ auction.end_time }}");
    console.log("End Time:", new Date(endTime)); 
    var currentTime = new Date();
    var timeLeft = Math.max(endTime - currentTime, 0);

    var days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
    var hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

    var formattedTime = formatTime(days, hours, minutes, seconds);

    // Update the timer text in the auction details
    document.getElementById('detail-timer').innerText = formattedTime;

    // Optionally, change the color based on time remaining
    document.getElementById('detail-timer').style.color = (timeLeft <= 60000) ? 'red' : 'green';
}

function formatTime(days, hours, minutes, seconds) {
    if (isNaN(days) || isNaN(hours) || isNaN(minutes) || isNaN(seconds)) {
        return '00d 00h 00m 00s';
    }
    return (days < 10 ? '0' : '') + days + 'd ' + (hours < 10 ? '0' : '') + hours + 'h ' + (minutes < 10 ? '0' : '') + minutes + 'm ' + (seconds < 10 ? '0' : '') + seconds + 's';
}

// Update the detail timer every second (adjust as needed)
setInterval(updateDetailTimer, 1000);

// Initial call to update the detail timer on page load
updateDetailTimer();

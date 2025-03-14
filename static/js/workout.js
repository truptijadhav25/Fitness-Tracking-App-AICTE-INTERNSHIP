document.addEventListener("DOMContentLoaded", function () {
    const startBtns = document.querySelectorAll(".start-btn");
    const modal = document.getElementById("workoutModal");
    const closeBtn = document.querySelector(".close");
    const workoutTitle = document.getElementById("workoutTitle");
    const countdown = document.getElementById("countdown");
    const progressBar = document.getElementById("progressBar");
    const startPauseBtn = document.getElementById("startPauseBtn");
    const durationInput = document.getElementById("workoutDuration");
    const endWorkoutBtn = document.getElementById("endWorkoutBtn");

    let timer;
    let timeLeft;
    let isRunning = false;
    let totalWorkoutTime;

    // Open modal
    startBtns.forEach(button => {
        button.addEventListener("click", function () {
            let workout = this.dataset.workout;
            workoutTitle.innerText = workout;
            modal.style.display = "block";
            resetTimer();
        });
    });

    // Close modal function
    function closeWorkoutModal() {
        modal.style.display = "none";
        clearInterval(timer);
        resetTimer();
    }

    // Close modal on X button
    closeBtn.addEventListener("click", closeWorkoutModal);

    // Close modal when clicking outside
    window.addEventListener("click", function (event) {
        if (event.target == modal) {
            closeWorkoutModal();
        }
    });

    // Reset Timer Function
    function resetTimer() {
        totalWorkoutTime = parseInt(durationInput.value) || 30; // Default 30 mins
        timeLeft = totalWorkoutTime * 60;
        updateDisplay();
        isRunning = false;
        startPauseBtn.innerText = "Start";
        clearInterval(timer);
    }

    // Start / Pause Timer
    startPauseBtn.addEventListener("click", function () {
        if (!isRunning) {
            totalWorkoutTime = parseInt(durationInput.value) || 30; // Update duration on start
            if (timeLeft === undefined || timeLeft === 0 || timeLeft > totalWorkoutTime * 60) {
                timeLeft = totalWorkoutTime * 60;
            }
            updateDisplay();
            timer = setInterval(updateTimer, 1000);
            startPauseBtn.innerText = "Pause";
        } else {
            clearInterval(timer);
            startPauseBtn.innerText = "Resume";
        }
        isRunning = !isRunning;
    });

    // Timer Countdown
    function updateTimer() {
        if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
        } else {
            clearInterval(timer);
            showWorkoutSummary(true);
        }
    }

    // Update Timer Display
    function updateDisplay() {
        let minutes = Math.floor(timeLeft / 60);
        let seconds = timeLeft % 60;
        countdown.innerText = `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
        progressBar.value = (timeLeft / (totalWorkoutTime * 60)) * 100;
    }

    // End Workout with Confirmation
    endWorkoutBtn.addEventListener("click", function () {
        let confirmEnd = confirm("Are you sure you want to end the workout?");
        if (confirmEnd) {
            clearInterval(timer);
            closeWorkoutModal();
            showWorkoutSummary(false);
        }
    });

    // Display Workout Summary
    function showWorkoutSummary(isCompleted) {
        let minutesSpent = totalWorkoutTime - Math.floor(timeLeft / 60);
        let caloriesBurned = (minutesSpent * 5).toFixed(1);

        // Remove existing modal before creating a new one
        let existingSummary = document.querySelector(".summary-modal");
        if (existingSummary) existingSummary.remove();

        const summaryModal = document.createElement("div");
        summaryModal.classList.add("summary-modal");
        summaryModal.innerHTML = `
            <div class="summary-content">
                <h2>${isCompleted ? "🎉 Workout Completed!" : "🏁 Workout Ended!"}</h2>
                <p>⏳ <strong>${minutesSpent} minutes</strong> of workout completed</p>
                <p>🔥 Estimated Calories Burned: <strong>${caloriesBurned} kcal</strong></p>
                <button id="closeSummary" class="summary-close-btn">Close</button>
            </div>
        `;

        document.body.appendChild(summaryModal);

        // Close Summary Modal
        document.getElementById("closeSummary").addEventListener("click", function () {
            summaryModal.classList.add("fade-out");
            setTimeout(() => summaryModal.remove(), 300);
        });
    }
});
document.addEventListener("DOMContentLoaded", function () {
    let heightSlider = document.getElementById("heightSlider");
    let heightDisplay = document.getElementById("heightDisplay");
    let waterIntakeElement = document.getElementById("waterIntake");

    function calculateWaterIntake(weight, duration) {
        let baseWater = weight * 0.04; // Standard: 40ml per kg
        if (duration > 30) baseWater += 0.5; // Extra hydration for longer workouts
        return `${baseWater.toFixed(2)} liters/day`;
    }

    function updateTable() {
        let age = document.getElementById("ageSlider").value;
        let heightCm = heightSlider.value;  
        let weight = document.getElementById("weightSlider").value;
        let duration = document.getElementById("durationSlider").value;
        let heartRate = document.getElementById("heartRateSlider").value;

        document.getElementById("ageValue").innerText = age;
        heightDisplay.innerText = `${heightCm} cm`;
        document.getElementById("weightValue").innerText = weight + " kg";
        document.getElementById("durationValue").innerText = duration + " min";
        document.getElementById("heartRateValue").innerText = heartRate + " bpm";

        // Fix water intake issue by adding a slight delay
        waterIntakeElement.innerText = "Calculating...";
        setTimeout(() => {
            waterIntakeElement.innerText = calculateWaterIntake(weight, duration);
        }, 500);
    }

    document.querySelectorAll("input[type='range'], input[name='gender']").forEach(input => {
        input.addEventListener("input", updateTable);
    });

    updateTable();
});





console.log('index.js');

// Import Sortable module
function closeAlertTimer() {
    setTimeout(function() {
        document.getElementById('alert').classList.add('slide-out');
    }, 5000);
}

function closeAlert() {
    var alert = document.getElementById('alert');
    alert.style.display = 'none';
}





    document.addEventListener('DOMContentLoaded', (event) => {
        console.log('DOMContentLoaded event fired');  // Add this line

        fetch('static/tooltip.json')
        .then(response => response.json())
        .then(data => {
            for (let key in data) {
                let el = document.querySelector(`#${key}`);
                if (el) {
                    el.setAttribute('data-tooltip', data[key]);
                }
            }
        });

        var tooltipElements = document.querySelectorAll('.tooltip-trigger');
        console.log('tooltipElements:', tooltipElements);  // Add this line
    tooltipElements.forEach((el) => {
        el.addEventListener('mousemove', (event) => {
            var tooltipText = el.getAttribute('data-tooltip');
            var tooltipElement = document.querySelector('.tooltip');
            if (!tooltipElement) {
                tooltipElement = document.createElement('div');
                tooltipElement.classList.add('tooltip');
                document.body.appendChild(tooltipElement);
            }
            tooltipElement.textContent = tooltipText;
            tooltipElement.style.left = (event.pageX - tooltipElement.offsetWidth / 2) + 'px';
            tooltipElement.style.top = (event.pageY + 20) + 'px';
        });
        el.addEventListener('mouseleave', (event) => {
            var tooltipElement = document.querySelector('.tooltip');
            if (tooltipElement) {
                tooltipElement.remove();
            }
        });
    });
});
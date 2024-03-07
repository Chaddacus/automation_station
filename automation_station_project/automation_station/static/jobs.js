console.log('jobs.js');

// Note that the path is the one you specified in your routing configuration
const socket = new WebSocket('wss://dev.auto.cloudwarriors.ai/ws/con/');

socket.onmessage = function(e) {

    //console.log('WebSocket message received:', e.data);
    const data = JSON.parse(e.data);

    if (data.command === 'update-table') {
        const jobs = data.jobs;
        const completed_jobs = data.completed_jobs;
        // Update the jobs table with the new data
        //updateTable('jobs', jobs);

        // Update the completed jobs table with the new data
        //updateTable('completed-jobs', completed_jobs);
        updateJobTables(jobs, completed_jobs);
        JobButton();
    }
};
 socket.onclose = function(e) {
     console.error('Chat socket closed - will appear during inital page load, but should not appear after that.');
 };
 socket.onerror = function(error) {
    console.error('WebSocket error:', error);
};
socket.addEventListener('open', function (event) {
    console.log('WebSocket is open now.');
    
    jobRedraw();
});


function jobRedraw() {

    console.log('jobRedraw');
    const message = JSON.stringify({ command: 'redraw' });
    socket.send(JSON.stringify({
        'message': message
    }));
    
     
    console.log(socket)    

    }
    
    

function JobButton() {

    let buttons = document.querySelectorAll('.websocket-run');
    console.log('buttons');
    console.log(buttons);
    let guids = [];
    buttons.forEach(button => {
    button.onclick = function(e) {
        console.log('clicked websocket-run button')
        const command = e.target.getAttribute('data-command');
        guids.push(e.target.getAttribute('data-guid'));
        const message = JSON.stringify({ command, guids });
        console.log(message);
        socket.send(JSON.stringify({
            'message': message
        }));
    };
                });
}

function jobSocket() {


let runSelectedButton = document.querySelector('.websocket-run-selected');
runSelectedButton.onclick = function(e) {
    console.log('clicked run-selected button')

    // Get all the rows in the job table
    let rows = document.querySelectorAll('.job-table tr');

    // Initialize an empty list to store the guids
    let guids = [];

    // Loop through each row
    rows.forEach(row => {
        // Get the checkbox in this row
        let checkbox = row.querySelector('.job-select');

        // If the checkbox is checked
        if (checkbox && checkbox.checked) {
            // Get the guid from the row (replace 'data-guid' with the correct attribute if it's different)
            let guid = row.getAttribute('data-guid');

            // Add the guid to the list
            guids.push(guid);
        }
    });

    // Send the list of guids through the WebSocket
    const message = JSON.stringify({ command: 'run-selected', guids });
    socket.send(JSON.stringify({
        'message': message
    }));

    //clear the checkboxes
    rows.forEach(row => {
        let checkbox = row.querySelector('.job-select');
        if (checkbox) {
            checkbox.checked = false;
        }
    });
    let checkbox = document.querySelector('.select-all');
    checkbox.checked = false;
};






let deleteSelectedButtons = document.querySelectorAll('.websocket-delete-selected');
deleteSelectedButtons.forEach(button => {
    button.onclick = function(e) {

        console.log('clicked delete-selected button')

        // Get all the rows in the job table

        let element = this.previousElementSibling;
            while (element && element.tagName.toLowerCase() !== 'table') {
                element = element.previousElementSibling;
            }
        let table = element;
        
        
        let rows = table.querySelectorAll('tr');

        // Initialize an empty list to store the guids
        let guids = [];

        let alertTrigger = false;

        // Loop through each row
        rows.forEach(row => {
            // Get the checkbox in this row
            let checkbox = row.querySelector('.job-select');
            console.log("checking checkbox");
            // If the checkbox is checked
            if (checkbox && checkbox.checked) {
                // Get the guid from the row (replace 'data-guid' with the correct attribute if it's different)
                let guid = row.getAttribute('data-guid');
                // if job status is not scheduled then throw an alert
                //let status = row.children[3].textContent;
                let status  = row.dataset.status
                console.log(status);
                
                if (status !== 'Scheduled' && status !== 'Executed') {
                    alert('Only scheduled or completed jobs can be deleted');
                    alertTrigger = true;
                    return;
                }


                // Add the guid to the list
                guids.push(guid);
            }
        });

        if (alertTrigger) {
            console.log("alert triggered")
            return;
        }
        // Confirm before sending the WebSocket message
        if (confirm('Are you sure you want to delete the selected jobs?')) {
            // Send the list of guids through the WebSocket
            const message = JSON.stringify({ command: 'delete-selected', guids });
            socket.send(JSON.stringify({
                'message': message
            }));
            //clear the checkboxes
            
        }
    };
});


let selectAllCheckbox = document.querySelector('.select-all');
selectAllCheckbox.onclick = function(e) {
    console.log('clicked select-all checkbox')

    // Get all the checkboxes in the job table
    let checkboxes = document.querySelectorAll('.job-table .job-select');

    // Loop through each checkbox
    checkboxes.forEach(checkbox => {
        // Set the checked property of the checkbox to the checked property of the select-all checkbox
        checkbox.checked = selectAllCheckbox.checked;
    });
};

}

function updateJobTables(jobs, completed_jobs) {

    const jobsTable = document.querySelector('#jobs');
    const completedJobsTable = document.querySelector('#completed-jobs');

    jobsTable.innerHTML =  jobs;
    completedJobsTable.innerHTML = completed_jobs;
}



function updateTable(tableId, tableData) {
    // Get the table and its body
    const table = document.querySelector(`#${tableId}`);
    let tbody = table.querySelector('tbody');

    // If the table doesn't have a tbody, create one
    if (!tbody) {
        tbody = document.createElement('tbody');
        table.appendChild(tbody);
    }

    // Clear the tbody
    tbody.innerHTML = '';

    // Add new rows to the tbody
    tableData.forEach(rowData => {
        const row = document.createElement('tr');
        row.dataset.guid = rowData.fields.job_id; // Set the data-guid attribute of the row

        // Create a new cell with a checkbox and add it to the row
        const checkboxCell = document.createElement('td');
        checkboxCell.className = 'border px-4 py-2'; // Set the class of the checkbox cell
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'job-select'; // Set the class of the checkbox
        checkbox.value = rowData.pk; // Use the primary key of the rowData as the value of the checkbox
        checkboxCell.appendChild(checkbox);
        row.appendChild(checkboxCell);

        // Get the fields of the rowData, excluding the job_id field
        const fields = { ...rowData.fields };
        delete fields.job_id;

        Object.values(fields).forEach(cellData => {
            const cell = document.createElement('td');
            cell.textContent = cellData;
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });
}
function sortableTable() {

    var el = document.getElementById('sortable-table-body');
    // Assign Sortable module to 'sortable' variable
    var sortable = Sortable.create(el);
    console.log('sortableTable');
    }
    
    document.addEventListener('DOMContentLoaded', (event) => {
        var tooltipElements = document.querySelectorAll('.tooltip-trigger');
        tooltipElements.forEach((el) => {
            el.addEventListener('mousemove', (event) => {
                var tooltipText = el.getAttribute('data-tooltip');
                var tooltipElement = document.querySelector('.tooltip');
                if (!tooltipElement) {
                    tooltipElement = document.createElement('div');
                    tooltipElement.classList.add('tooltip');
                    tooltipElement.textContent = tooltipText;
                    document.body.appendChild(tooltipElement);
                }
                console.log(event.pageX, event.pageY, tooltipElement.offsetWidth, tooltipElement.offsetHeight);
                tooltipElement.style.left = (event.pageX - tooltipElement.offsetWidth + 100) + 'px';
                tooltipElement.style.top = event.pageY + 'px';
            });
            el.addEventListener('mouseleave', (event) => {
                var tooltipElement = document.querySelector('.tooltip');
                if (tooltipElement) {
                    tooltipElement.remove();
                }
            });
        });
    });

// In your JavaScript code

$("#dt-basic").DataTable({
    searching: true
});

    $('#dt-buttons').DataTable({
        dom: '<"row p-2"<"col-md-6"B><"col-md-6"f>>rtip',
        buttons: [
            {
                text: 'Custom Button',
                action: function (e, dt, node, config) {
                    alert('Custom Button Clicked');
                }
            },
            'print','excel','csv','pdf'
        ]
    });

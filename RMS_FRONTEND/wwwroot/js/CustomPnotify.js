//https://www.cssscript.com/toast-simple-notify/
$(".pnotify-success").on("click", function () {
    PNotify.success({
        title: $(this).attr('data-title'),
        text: $(this).attr('data-message'),
        styling: 'bootstrap5',
        icon: 'fa-solid fa-check f-20 mx-2 mt-2',
        className: 'bg-success text-white'
    });
});
$(".pnotify-error").on("click", function () {
    PNotify.error({
        title: $(this).attr('data-title'),
        text: $(this).attr('data-message'),
        styling: 'bootstrap5',
        icon: 'fa-solid fa-xmark f-20 mx-2 mt-2',
        className: 'bg-success text-white'
    });
});
$(".pnotify-info").on("click", function () {
    PNotify.info({
        title: $(this).attr('data-title'),
        text: $(this).attr('data-message'),
        styling: 'bootstrap5',
        icon: 'fa-solid fa-info f-20 mx-2 mt-2',
        className: 'bg-success text-white'
    });
});




























































































//function notify(type, message) {
//    var icon;
//    var title;
//    var msgType = type.trim();
//    switch (msgType) {
//        case 'danger':
//            title = 'Error! '
//            icon = 'fa-solid fa-xmark f-20 mx-2 mt-2'
//            break;
//        case 'success':
//            title = 'Success! '
//            icon = 'fa-solid fa-check f-20 mx-2 mt-2'
//            break;
//        case 'warning':
//            title = 'Warning! '
//            icon = 'fa-solid fa-triangle-exclamation f-20 mx-2 mt-2';
//            break;
//        case 'info':
//            title = 'Info! '
//            icon = `fa-solid fa-info f-20 mx-2 mt-2`
//            break;
//        default:
//        //    toastr.info(message)
//    }

//    $.growl({
//        icon: icon,
//        title: title,
//        message: message,
//        url: ''
//    }, {
//        element: 'body',
//        type: type,
//        allow_dismiss: true,
//        placement: {
//            from: 'top',
//            align: 'right'
//        },
//        offset: {
//            x: 30,
//            y: 30
//        },
//        spacing: 10,
//        z_index: 999999999999,
//        delay: 2500,
//        timer: 1000,
//        url_target: '_blank',
//        mouse_over: false,
//        animate: {
//            enter: 'animated fadeInRight',
//            exit: 'animated fadeOutRight'
//        },
//        icon_type: 'class',
//        template: '<div data-growl="container" class="alert  px-2 " role="alert">' +
//            '<span data-growl="icon" ></span>' +
//            '<strong data-growl="title"></strong>' +
//            '<span data-growl="message"></span>' +
//            '<a href="#" data-growl="url"></a>' +
//            '</div>'
//    });
//};

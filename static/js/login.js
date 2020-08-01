$(document).ready(function() {
    $('#pass-form').submit(function(e) {
        e.preventDefault();
        login();
        return false;
    });
});

function login() {
    let password = $('#input-password').val();
    console.log('pass: ' + password);
    // $('#pass-form').pass.value = password;
    $.ajax({
        type: "POST",
        url: "/login/auth",
        data: JSON.stringify(password),
        success: function(response)
        {
            // add 'remember me' cookie
            console.log(response);
            window.location.replace(response);
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}

function logout() {
    $.ajax({
        type: "POST",
        url: '/logout',
        data: JSON.stringify(''),
        success: function(response)
        {
            // remove 'remember me' cookie
            window.location.replace(response);
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}
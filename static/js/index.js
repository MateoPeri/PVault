const card = `
<div class="col mb-4">
    <div class="card h-100">
        <div class="embed-responsive embed-responsive-16by9">
            <img id="card_img" src="" class="card-img-top embed-responsive-item" alt="...">
        </div>
        <div class="card-body">
            <h5 class="card-title"><a id="card_title" target="_blank">Card title</a></h5>
            <p id="card_desc" class="card-text"></p>
        </div>
    </div>
</div>
`;

let defElemModal;
let urlParams;

let tags;
$(document).ready(function() {
    console.log('ready!');
    urlParams = new URLSearchParams(window.location.search);

    retrieve_elems();
    $("#refresh_but").on("click", function() {
       retrieve_elems();
    });
    $("#upload_but").on("click", function() {
        // $("#web-upload-form").trigger("reset");
        clearForm($("#web-tab"));
        // $("#file-upload-form").trigger("reset");
        clearForm($("#file-tab"));
        tags = [];
        list_tags(tags, $("#up_tag_parent"))
        $('#uploadModal').modal('show');
    });
    $("#del_but").on("click", function() {
        remove_elem();
    });

    let up_tag = $("#up_tag_form");
    up_tag.find('.btn').on("click", function() {
        let v = up_tag.find('#tags-label').val().trim();
        up_tag.find('#tags-label').val("");
        up_tag.find('#tags-label').text("");
        let p = $("#up_tag_parent");
        add_tag_to_parent(v, p);
    });
    let view_tag = $("#view_tag_form");
    view_tag.find('.btn').on("click", function() {
        let v = view_tag.find('#tags-label').val().trim();
        view_tag.find('#tags-label').val("");
        let p = $("#view_tag_parent");
        add_tag_to_parent(v, p);
    });
    up_tag.find('#tags-label').keyup(function(event) {
        if (event.keyCode === 13) {
            up_tag.find('.btn').click();
        }
    })
    view_tag.find('#tags-label').keyup(function(event) {
        if (event.keyCode === 13) {
            view_tag.find('.btn').click();
        }
    });

    $("#edit_but").on("click", function() {
        toggle_edit();
    });
    $("#save_but").on("click", function() {
        save_changes();
    });

    $("#search-but").on("click", function (e) {
        e.preventDefault();
        search_by(sch_inp.val());
    });
    let sch_inp = $("#search-inp");
    sch_inp.val(urlParams.get('q'));
    sch_inp.keyup(function(event) {
        if (event.keyCode === 13) {
            $("#search-but").click();
        }
    })

    defElemModal = $('#elemModal').clone(true, true);
    //$('#elemModal').data2('old-state', $('#elemModal').html());
});

function clearForm($form)
{
    $form.find(':input').not(':button, :submit, :reset, :hidden, :checkbox, :radio').val('');
    $form.find(':checkbox, :radio').prop('checked', false);
}

let newCard;
let elems, selected_elem;
const tagHTML = `<a href="#" class="badge badge-primary">Test</a>`;

let isEditing;

function toggle_edit() {
    let $div=$('#elemModal').find('.editable');
    let edit = $div.prop('contenteditable');
    isEditing = edit !== 'true';

    $("#edit_but").text(isEditing ? 'Done' : 'Edit');
    $('#elemModalTitle').text(isEditing ? selected_elem["location"]["location"] : selected_elem["name"]);

    $div.prop('contenteditable', isEditing);
}

function list_tags(tgs, p) {
    p.html("");
    for (let i = 0; i < tgs.length; i++) {
        const e = tgs[i];
        let newTag = $(tagHTML);
        newTag.text(e);
        // tag.attr("href")
        newTag.on("click", {
            t: e,
            p: p
        }, tag_clicked );
    
        p.append(newTag);
        p.append("&nbsp;");
    }
}

function add_tag_to_parent(val, parent) {
    let newTag = $(tagHTML);
    if (tags.includes(val))
        return
    
    tags.push(val);

    newTag.text(val);
    // tag.attr("href")
    newTag.on("click", {
        t: val
    }, tag_clicked );

    parent.append(newTag);
    parent.append("&nbsp;");
}

function tag_clicked(event) {
    if (isEditing)
        remove_tag(event);
    else
        filter_by_tag(event);
}

function remove_tag(event) {
    let index = tags.indexOf(event.data.t);
    tags.splice(index, 1);

    list_tags(tags, event.data.p);
}

function filter_by_tag(event) {
    console.log("Filtering by " + event.data.t);
    document.location.search = updateUrlParameter(document.location.search, 't', event.data.t);
}

function search_by(query) {
    document.location.search = updateUrlParameter(document.location.search, 'q', query);
}

function save_changes() {
    let url = '/edit';
    let elem = selected_elem;
    elem["name"] = $('#elemModalLabel').text();
    elem["location"]["preview"]["image"] = $('#elemModalImage').attr("src");
    elem["location"]["location"] = $('#elemModalTitle').attr("href");
    elem["location"]["preview"]["desc"] = $('#elemText').text();
    elem["tags"] = tags;
    tags = []

    let data = JSON.stringify(elem);
    // console.log(data);
    $.ajax({
        type: "POST",
        url: url,
        data: data, // element to edit
        success: function()
        {
            $('#elemModal').modal('hide');
            retrieve_elems();
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}

function retrieve_elems() {
    $('#card_parent').html("");
    let url = '/get_elems';
    let paramObj = {};
    for (let value of urlParams.keys()) {
        paramObj[value] = urlParams.get(value);
    }
    $.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(paramObj), // number of elements to retrieve
        success: function(response)
        {            
            elems = JSON.parse(response);
            console.log(elems);
            for (let i = 0; i < elems.length; i++) {
                const e = elems[i];
                newCard = $(card);
                $(newCard).find('#card_title').text(e["name"]);
                $(newCard).find('#card_desc').text(e["location"]["preview"]["desc"]);
                $(newCard).find('#card_img').attr("src", e["location"]["preview"]["image"]);
                $(newCard).find('#card_title').attr("href", e["location"]["location"]);
                $(newCard).find('#card_img').on("click", {
                    el: e
                  }, show_element );
                $('#card_parent').append(newCard);
            }
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}

function remove_elem() {
    let url = '/del';
    let data = JSON.stringify(selected_elem["uuid"]);
    console.log(data)
    console.log(data);
    $.ajax({
        type: "POST",
        url: url,
        data: data, // element to remove
        success: function()
        {
            $('#elemModal').modal('hide');
            retrieve_elems();
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}

function submit_url() {
    let url = '/add_url';
    let data = {"elem": $("#url-field").val(),
                "name": $("#url-title-field").val(),
                "tags": tags, "archive": $("#archive-check").is(":checked")}
    tags = []
    data = JSON.stringify(data);
    // console.log(data);
    $.ajax({
        type: "POST",
        url: url,
        data: data, // element to add
        success: function()
        {
            $("#url-field").val("");
            $("#url-title-field").val("");
            $('#uploadModal').modal('hide');
            retrieve_elems();
        },
        error: function(data)
        {
            alert('ERROR\n' + data.responseText);
            console.log(data)
        },
    });
}

function show_element(event) {
    selected_elem = event.data.el;
    // console.log(selected_elem["name"]);
    // reset modal
    let elem_modal = $('#elemModal');
    // TODO: ??? elem_modal.replaceWith(defElemModal.clone(true, true));

    elem_modal.modal('show');
    $('#elemModalLabel').text(selected_elem["name"]);
    $('#elemModalImage').attr("src", selected_elem["location"]["preview"]["image"]);
    $('#elemModalTitle').attr("href", selected_elem["location"]["location"]).text(selected_elem["name"]);
    $('#elemText').text(selected_elem["location"]["preview"]["desc"]);

    tags = selected_elem["tags"];
    list_tags(tags, $("#view_tag_parent"));

    isEditing = false;
    elem_modal.find('.editable').prop('contenteditable', isEditing);
}

// https://gist.github.com/niyazpk/f8ac616f181f6042d1e0#gistcomment-1743025
function updateUrlParameter(uri, key, value) {
    // remove the hash part before operating on the uri
    let i = uri.indexOf('#');
    let hash = i === -1 ? ''  : uri.substr(i);
    uri = i === -1 ? uri : uri.substr(0, i);

    let re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
    let separator = uri.indexOf('?') !== -1 ? "&" : "?";

    if (!value) {
        // remove key-value pair if value is empty
        uri = uri.replace(new RegExp("([?&]?)" + key + "=[^&]*", "i"), '');
        if (uri.slice(-1) === '?') {
          uri = uri.slice(0, -1);
        }
        // replace first occurrence of & by ? if no ? is present
        if (uri.indexOf('?') === -1) uri = uri.replace(/&/, '?');
    } else if (uri.match(re)) {
        uri = uri.replace(re, '$1' + key + "=" + value + '$2');
    } else {
        uri = uri + separator + key + "=" + value;
    }
    return uri + hash;
}
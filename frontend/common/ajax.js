export function POST (url, data) {
    var csrf = $("#csrf-middleware-token").val();

    return $.ajax({
        method: "POST",
        url: url,
        headers: {
            "X-CSRFToken": csrf
        },
        data: data
    })
}
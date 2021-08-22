

function register1() {
    let mid = document.querySelector("#reg-mid");
    let orig = document.querySelector("#orig");
    orig.style.display = "none";
    mid.style.display = "block";
}

function register2()    {
    let ranger = document.querySelector("#reg-mid-range");
    let mid = document.querySelector("#reg-mid");
    let final = document.querySelector("#reg-final");
    if (ranger.valueAsNumber < 70)  {
        window.alert("close this window when you're ready to answer properly");
    }
    else{
        mid.style.display = "none";
        final.style.display = "block";
    }
}

function login1() {
    let mid = document.querySelector("#log-mid");
    let orig = document.querySelector("#orig");
    orig.style.display = "none";
    mid.style.display = "block";
}

function login2()    {
    let ranges = document.querySelector("#log-mid-range");
    let mid = document.querySelector("#log-mid");
    let next = document.querySelector("#log-mid-message");
    let final = document.querySelector("#log-final");
    let message = document.querySelector("#log-message");
    if (ranges.valueAsNumber < 40)  {
        message.innerHTML = "Not having a good day eh?";
        mid.style.display = "none";
        next.style.display = "block";
    }
    else{
        mid.style.display = "none";
        final.style.display = "block";
    }
}

function login3()   {
    let mid = document.querySelector("#log-mid-message");
    let final = document.querySelector("#log-final");
    mid.style.display = "none";
    final.style.display = "block";
}


function chngrespect(fish_id, page, type)   {
    document.querySelector(`#r-${fish_id}`).disabled = true;
    document.querySelector(`#d-${fish_id}`).disabled = true;
    let message = document.querySelector(`#R-${fish_id}`);
    if (type === 'resp')    {
        resp = {
            "fishid": fish_id,
            "type": "resp"
        };
        var audio = new Audio("static/Trumpet-Fanfare.wav");
        audio.play();
    }
    else    {
        resp = {
            "fishid": fish_id,
            "type": "diss"
        };
    }
    $.post("/respect", resp, function(datar, status) {
        if (page === 'rivs')    {
            /* rivals */
            document.querySelector(`#i-${fish_id}`).innerHTML = "Respect: " + datar["respect"];
        }
        else{
            /* lookup */
            document.querySelector(`#i-${fish_id}`).innerHTML = "With " + datar["respect"] + " respect";
        }
        if (datar["done"] === false && type === 'resp')    {
            message.innerHTML = "RESPECTED";
        }
        if (datar["done"] === false && type === 'diss') {
            message.innerHTML = "DISRESPECTED";
        }
    });
};


function selectParentsPost(fish_id, MorF)   {
    data = {
        "fish_id": fish_id
    };
    $.post("/idfish", data, function(response)  {
        if (MorF === "MOTHER")  {
            document.querySelector("#mpic").src = `static/images/${response.species}.jpg`;
            document.querySelector("#mbio").innerHTML = response.name + " the " + response.species;
            document.querySelector("#mtext").innerHTML = response.time;
        }
        else if (MorF === "FATHER") {
            document.querySelector("#fpic").src = `static/images/${response.species}.jpg`;
            document.querySelector("#fbio").innerHTML = response.name + " the " + response.species;
            document.querySelector("#ftext").innerHTML = response.time;
        }
        else {
            alert("error with the js parent selector");
        };
    })
}


jQuery(document).ready(function($){
    $.post("/notifications", function(response) {
        if (response.new === "some")  {
            var bell = document.querySelector("#bell");
            bell.style.backgroundColor = "red";
        }
    })
    $(document).on('submit', '.comform', function(event){
        event.preventDefault();
        var comment = this.commentstr.value;
        var id = this.fish_id.value;
        info = {
            "commentstr": comment,
            "fish_id": id
        };
        $.post("/addcomment", info, function(response)  {
            if (response.commentstr != undefined)  {
                newcomment = document.getElementById(`newcom-${id}`);
                newcomment.innerHTML = response.username + ": \"" + response.commentstr + "\"" + " (just now)";
                newcomment.style.display = "block";
            }
            var texts = document.getElementsByName("commentstr");
            var i;
            /* clears the text fields */
            for (i = 0; i < texts.length; i++)  {
                texts[i].value = "";
            }
        });
    });

    $(document).on('click', '.comformlookup', function(event){
        event.preventDefault();
        var id = this.value;
        info = {
            "fish_id": id
        };
        $.post("/viewcomments", info, function(response)  {
            const parent = document.getElementById(`list-${id}`);
            /* clears the list so response is not appended every time this button is pressed */
            parent.textContent = '';
            if (response.length === 0)  {
                var para = document.createElement("P");
                para.innerHTML = "No comments :(";
                parent.appendChild(para);
            }
            else    {
                var i;
                for (i = 0; i < response.length; i++)   {
                    var para = document.createElement("P");
                    para.innerHTML = response[i].username + ": \"" + response[i].comment + "\" (" + response[i].time + ")";
                    para.style = "background-color: cornsilk; margin-left: 10px; border-radius: 5px; padding: 5px;";
                    parent.appendChild(para);
                }
            }
        });
    });
});

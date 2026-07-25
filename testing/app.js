const API_URL =
    "http://127.0.0.1:3000/api/scan";


let results = [];



function loadPrompts() {


    let filter =
        document.getElementById(
            "categoryFilter"
        ).value;


    let html = "";


    prompts
        .filter(x =>
            !filter ||
            x.category === filter
        )
        .forEach(p => {


            html += `

<div class="card">

<h3>${p.name}</h3>

<b>
Category:
${p.category}
</b>

<p>
${p.prompt}
</p>


<button onclick="runPrompt(${p.id})">
Test
</button>


<button onclick="deletePrompt(${p.id})">
Delete
</button>


</div>

`;

        });


    document.getElementById(
        "promptList"
    ).innerHTML = html;


}



async function scan(prompt) {


    let payload = {

        prompt: prompt,

        client_id:
            "d5e8bf75-cfbc-45fa-bafa-0b3e11d8a243",

        source:
            "chatgpt.com",

        user_agent:
            navigator.userAgent

    };



    let response =
        await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(payload)

        });


    return await response.json();

}



async function runPrompt(id) {


    let item =
        prompts.find(
            x => x.id === id
        );


    let result =
        await scan(item.prompt);



    results.push({

        prompt: item.name,

        response: result

    });


    document.getElementById(
        "result"
    ).textContent =
        JSON.stringify(
            result,
            null,
            2
        );

}



async function testCustom() {


    let prompt =
        document.getElementById(
            "customPrompt"
        ).value;


    let result =
        await scan(prompt);


    document.getElementById(
        "result"
    ).textContent =
        JSON.stringify(
            result,
            null,
            2
        );

}



async function runAll() {


    results = [];


    for (let p of prompts) {


        console.log(
            "Testing",
            p.name
        );


        let response =
            await scan(p.prompt);



        results.push({

            id: p.id,

            name: p.name,

            expected:
                p.expected,

            response

        });


    }


    downloadResults();


    alert(
        "Completed " + results.length + " tests"
    );


}



function downloadResults() {


    let blob =
        new Blob(

            [
                JSON.stringify(
                    results,
                    null,
                    2
                )
            ],

            {
                type: "application/json"
            }

        );



    let a =
        document.createElement("a");


    a.href =
        URL.createObjectURL(blob);


    a.download =
        "detector-results.json";


    a.click();

}



function deletePrompt(id) {

    let index =
        prompts.findIndex(
            x => x.id === id
        );


    if (index > -1) {

        prompts.splice(
            index,
            1
        );

        loadPrompts();

    }

}



loadPrompts();
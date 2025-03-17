$(document).ready(function () {
    initializeAnimations();
    initializeFlow(); // Ensure Flow starts in correct position with "Standing by"
});

function initializeAnimations() {
    const animations = ["analysis", "creation", "reassignment", "debt"];
    animations.forEach(name => {
        let container = document.getElementById(`lottie-${name}`);
        if (container) {
            container.innerHTML = `<object type="image/svg+xml" data="/static/animations/${name}.svg" class="svg-animation"></object>`;
        }
    });
}

function initializeFlow() {
    if ($('#flow-box').length === 0) {
        $('.agent-container').before('<div id="flow-box" class="flow-box">Standing by</div>');
    }
}

function sendChat() {
    let query = $('#user_input').val().trim();
    if (query === '') return;

    appendMessage("user-msg", query);
    $('#user_input').val('');

    resetAgents();
    resetFlow();
    appendMessage("bot-msg", "Analyzing your query...", "loading");

    // Dynamically initialize the flow
    updateFlow("User");

    $.post('/ask', { query: query }, function (data) {
        processChatResponse(data);
    });
}

function processChatResponse(data) {
    resetAgents();
    resetFlow();

    let flowSteps = ["User"]; // Start with User dynamically

    setTimeout(() => {
        if (data.assigned_team.includes("Incident Analysis")) {
            activateAgent('analysis_agent');
            flowSteps.push("Incident Analysis");
        }
    }, 500);

    setTimeout(() => {
        if (data.assigned_team.includes("Tech Debt Analysis")) {
            activateAgent('debt_agent');
            flowSteps.push("Tech Debt Analysis");
        }
    }, 1000);

    setTimeout(() => {
        if (data.assigned_team.includes("Incident Creation") || data.incident_number) {
            activateAgent('creation_agent'); // ✅ Fix: Activate Creation Agent
            flowSteps.push("Create Incident");
        }
    }, 1200);

    setTimeout(() => {
        $('#loading').remove();
        appendMessage("bot-msg", formatResponse(data.response));

        let techDebtContent = generateTechDebtContent(data.tech_debt_suggestions);
        if (techDebtContent) {
            appendMessage("bot-msg", techDebtContent);
        }

        flowSteps.push("End");
        updateFlow(flowSteps.join(" ➝ ")); // Ensure dynamic order update
    }, 1500);
}

function activateAgent(agentId) {
    $('#' + agentId).addClass('agent-active').css('border', '3px solid #002f6c');
}

function resetAgents() {
    $('.agent-box').removeClass('agent-active').css('border', 'none');
}

function resetFlow() {
    $('#flow-box').text("Standing by"); // Reset to "Standing by"
}

function updateFlow(newFlowText) {
    let flowBox = $('#flow-box');
    if (flowBox.length === 0) {
        $('.agent-container').before('<div id="flow-box" class="flow-box"></div>');
        flowBox = $('#flow-box');
    }
    flowBox.text(newFlowText);
}

function appendMessage(className, message, id = "") {
    let msgElement = `<div class="message ${className}" ${id ? `id="${id}"` : ''}>${message}</div>`;
    $('#chat_box').append(msgElement);
    $('#chat_box').scrollTop($('#chat_box')[0].scrollHeight);
}

function formatResponse(response) {
    return response.replace(/\n/g, "<br>");
}

function generateTechDebtContent(techDebt) {
    if (!techDebt || techDebt === "No significant tech debt identified.") return "";    

    let formattedTechDebt = techDebt
        .replace(/Agent: Tech Debt Agent\s+/g, "") // Remove duplicate agent labels
        .replace(/\n/g, "<br>")                    // Ensure new lines render in HTML
        .replace(/- /g, "- ");                     // Convert "-" to "•" for better readability

    return `Agent: Tech Debt Agent<br><br>
        ${formattedTechDebt}`;
}

function resetChat() {
    $('#chat_box').empty(); // Clear the chat box
    $('#user_input').val(''); // Reset the input box
    resetFlow(); // Reset flow to "Standing by"
    resetAgents(); // Remove agent highlights
}

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
    }).fail(function () {
        appendMessage("bot-msg error-msg", "Error processing your request. Please try again.");
        resetFlow();
    });
}

function processChatResponse(data) {
    resetAgents();
    resetFlow();

    let flowSteps = ["User"];

    setTimeout(() => {
        if (data.assigned_team.includes("Incident Analysis")) {
            activateAgent('analysis_agent');
            flowSteps.push("Incident Analysis");
        }
    }, 500);

    setTimeout(() => {
        if (data.assigned_team.includes("Tech Debt Analysis") && data.tech_debt_suggestions) {
            activateAgent('debt_agent');
            flowSteps.push("Tech Debt Analysis");
        }
    }, 1000);

    setTimeout(() => {
        if (data.assigned_team.includes("Incident Creation") || data.incident_number) {
            activateAgent('creation_agent');
            flowSteps.push("Create Incident");
        }
    }, 1200);

    setTimeout(() => {
        $('#loading').remove();
        appendMessage("bot-msg", formatResponse(data.response));

        let techDebtContent = generateTechDebtContent(data.tech_debt_suggestions);
        if (techDebtContent) {
            appendMessage("tech-debt-msg highlight-box", techDebtContent); // 🔥 Highlighted Box for Tech Debt
        }

        flowSteps.push("End");
        updateFlow(flowSteps.join(" ➝ "));
    }, 1500);
}

function activateAgent(agentId) {
    $('#' + agentId).addClass('agent-active').css('border', '3px solid #002f6c');
}

function resetAgents() {
    $('.agent-box').removeClass('agent-active').css('border', 'none');
}

function resetFlow() {
    $('#flow-box').text("Standing by");
}

function updateFlow(newFlowText) {
    let flowBox = $('#flow-box');
    if (flowBox.length === 0) {
        $('.agent-container').before('<div id="flow-box" class="flow-box"></div>');
        flowBox = $('#flow-box');
    }
    flowBox.text(newFlowText);
}

function appendMessage(className, message) {
    let msgElement = `<div class="message ${className}">${message}</div>`;
    $('#chat_box').append(msgElement);
    $('#chat_box').scrollTop($('#chat_box')[0].scrollHeight);
}

function formatResponse(response) {
    return response.replace(/\n/g, "<br>");
}

function generateTechDebtContent(techDebt) {
    if (!techDebt || techDebt === "No significant tech debt identified.") return "";

    // Ensure "Agent: Tech Debt Agent" isn't added twice
    if (!techDebt.includes("Agent: Tech Debt Agent")) {
        techDebt = `<strong>Agent: Tech Debt Agent</strong><br><br>` + techDebt;
    }

    return `
        <div class="tech-debt-box highlight-box">
            ${techDebt.replace(/\n/g, "<br>")}
        </div>`;
}


function resetChat() {
    $('#chat_box').empty();
    $('#user_input').val('');
    resetFlow();
    resetAgents();
}

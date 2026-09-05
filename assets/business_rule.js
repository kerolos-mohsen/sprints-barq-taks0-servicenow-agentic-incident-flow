(function executeRule(current, previous /*null when async*/) {
    try {
        var payload = {
            "incident_sys_id": current.getValue('sys_id'),
            "number": current.getValue('number'),
            "short_description": current.getValue('short_description'),
            "description": current.getValue('description'),
            "priority": parseInt(current.getValue('priority'), 10)
        };

        var r = new sn_ws.RESTMessageV2();
        // Replace YOUR_NGROK_URL with your public ngrok URL (e.g. https://pauper-bronchial-studied.ngrok-free.dev)
        // and YOUR_WEBHOOK_SECRET with the secret configured in your .env
        r.setEndpoint('YOUR_NGROK_URL/api/v1/webhook');
        r.setHttpMethod('POST');
        r.setRequestHeader('Content-Type', 'application/json');
        r.setRequestHeader('X-Webhook-Secret', 'YOUR_WEBHOOK_SECRET');
        r.setRequestBody(JSON.stringify(payload));
        r.executeAsync();

        gs.info('Task0: sent incident ' + current.getValue('number'));
    } catch (ex) {
        gs.error('Task0: failed to send incident: ' + ex.message);
    }
})(current, previous);

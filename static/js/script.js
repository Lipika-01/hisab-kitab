function generateMemberFields() {
    const memberCountInput = document.getElementById("member_count");
    const memberFieldsDiv  = document.getElementById("memberFields");
    memberFieldsDiv.innerHTML = "";
    const count = parseInt(memberCountInput.value);
    if (isNaN(count) || count < 1) {
        memberFieldsDiv.innerHTML =
            "<p class='error-message'>⚠ Please enter a valid number of people.</p>";
        return;
    }

    // Member 1 = logged-in user (read-only)
    const firstInput       = document.createElement("input");
    firstInput.type        = "text";
    firstInput.name        = "member_1";
    firstInput.value       = CURRENT_USERNAME;
    firstInput.readOnly    = true;
    firstInput.className   = "member-input";
    memberFieldsDiv.appendChild(firstInput);

    // Remaining members
    for (let i = 2; i <= count; i++) {
        const input       = document.createElement("input");
        input.type        = "text";
        input.name        = `member_${i}`;
        input.placeholder = `Username of member ${i}`;
        input.required    = true;
        input.className   = "member-input";
        memberFieldsDiv.appendChild(input);
    }
}
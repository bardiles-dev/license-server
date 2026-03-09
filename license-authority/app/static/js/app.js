(function() {
    "use strict";
    const form = document.getElementById("formCreate");
    if (!form) return;
    const licenseType = document.getElementById("licenseType");
    const wrapMachineLock = document.getElementById("wrapMachineLock");
    const wrapMaxActivations = document.getElementById("wrapMaxActivations");
    const maxActivations = document.getElementById("maxActivations");

    function toggleMachineFields() {
        const isMachine = licenseType.value === "machine";
        wrapMachineLock.classList.toggle("d-none", !isMachine);
        wrapMachineLock.querySelector("#machineLock").required = isMachine;
        if (isMachine) {
            maxActivations.value = "1";
            wrapMaxActivations.classList.add("d-none");
        } else {
            wrapMaxActivations.classList.remove("d-none");
        }
    }
    licenseType.addEventListener("change", toggleMachineFields);
    toggleMachineFields();

    var featureCount = 1;
    document.getElementById("addFeature").addEventListener("click", function() {
        var div = document.createElement("div");
        div.className = "input-group mb-2";
        div.innerHTML = "<input type=\"text\" class=\"form-control\" placeholder=\"id\" name=\"f_id_" + featureCount + "\">" +
            "<input type=\"text\" class=\"form-control\" placeholder=\"version\" name=\"f_version_" + featureCount + "\">" +
            "<input type=\"text\" class=\"form-control\" placeholder=\"funcionality\" name=\"f_funcionality_" + featureCount + "\">";
        document.getElementById("featuresList").appendChild(div);
        featureCount++;
    });

    form.addEventListener("submit", async function(e) {
        e.preventDefault();
        var btn = document.getElementById("btnCreate");
        btn.disabled = true;
        var fd = new FormData(form);
        var features = [];
        for (var i = 0; i < featureCount; i++) {
            var id = fd.get("f_id_" + i);
            if (id && id.toString().trim()) {
                features.push({
                    id: id.toString().trim(),
                    version: (fd.get("f_version_" + i) || "").toString().trim() || null,
                    funcionality: (fd.get("f_funcionality_" + i) || "").toString().trim() || null
                });
            }
        }
        var body = {
            company: fd.get("company").toString().trim(),
            license_type: fd.get("license_type"),
            max_activations: parseInt(fd.get("max_activations") || "1", 10),
            duration_days: parseInt(fd.get("duration_days") || "365", 10),
            features: features.length ? features : null
        };
        if (licenseType.value === "machine") {
            body.machine_lock = fd.get("machine_lock").toString().trim();
        } else {
            body.machine_lock = null;
        }
        try {
            var r = await fetch("/create", {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (r.status === 401) { window.location.href = "/login"; return; }
            var data = await r.json();
            if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
            document.getElementById("resultInstallString").value = fd.get("company").toString()+ "_" + data.license_install_string || "";
            document.getElementById("resultPayload").textContent = JSON.stringify({ payload: data.payload, signature: data.signature }, null, 2);
            new bootstrap.Modal(document.getElementById("resultModal")).show();
        } catch (err) {
            alert("Error: " + (err.message || err));
        }
        btn.disabled = false;
    });

    document.getElementById("copyInstallString").addEventListener("click", function() {
        var ta = document.getElementById("resultInstallString");
        ta.select();
        navigator.clipboard.writeText(ta.value);
        this.textContent = "\u2713";
        var self = this;
        setTimeout(function() { self.textContent = "\uD83D\uDCCB"; }, 1500);
    });

    var licensesSection = document.querySelector(".table-responsive");
    if (licensesSection) {
        licensesSection.addEventListener("click", function(e) {
            var renewBtn = e.target.closest(".renew-btn");
            var revokeBtn = e.target.closest(".revoke-btn");
            if (renewBtn) {
                var licenseId = renewBtn.getAttribute("data-license-id");
                if (licenseId) {
                    document.getElementById("renewLicenseId").value = licenseId;
                    new bootstrap.Modal(document.getElementById("renewModal")).show();
                }
                return;
            }
            if (revokeBtn) {
                var licenseId = revokeBtn.getAttribute("data-license-id");
                if (!licenseId) return;
                if (!confirm("\u00BFRevocar esta licencia?")) return;
                (async function() {
                    try {
                        var r = await fetch("/revoke/" + encodeURIComponent(licenseId), {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            credentials: "same-origin"
                        });
                        if (r.status === 401) { window.location.href = "/login"; return; }
                        var data = (r.headers.get("content-type") || "").indexOf("application/json") !== -1 ? await r.json() : {};
                        if (!r.ok) throw new Error(data.detail || data.message || "Error " + r.status);
                        location.reload();
                    } catch (err) {
                        alert("Error: " + (err.message || err));
                    }
                })();
            }
        });
    }

    var btnRenew = document.getElementById("btnRenewConfirm");
    if (btnRenew) {
        btnRenew.addEventListener("click", async function() {
            var licenseId = document.getElementById("renewLicenseId").value.trim();
            if (!licenseId) {
                alert("Falta el ID de licencia.");
                return;
            }
            var extraDays = parseInt(document.getElementById("renewExtraDays").value, 10) || 365;
            var btn = this;
            btn.disabled = true;
            try {
                var r = await fetch("/renew/" + encodeURIComponent(licenseId), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    credentials: "same-origin",
                    body: JSON.stringify({ extra_days: extraDays })
                });
                if (r.status === 401) { window.location.href = "/login"; return; }
                var data = (r.headers.get("content-type") || "").indexOf("application/json") !== -1 ? await r.json() : {};
                if (!r.ok) throw new Error(Array.isArray(data.detail) ? (data.detail[0] && data.detail[0].msg) || JSON.stringify(data.detail) : (data.detail || data.message || "Error " + r.status));
                document.getElementById("resultInstallString").value = data.license_install_string || "";
                document.getElementById("resultPayload").textContent = JSON.stringify({ payload: data.payload, signature: data.signature }, null, 2);
                var renewModalEl = document.getElementById("renewModal");
                var modalInstance = bootstrap.Modal.getInstance(renewModalEl);
                if (modalInstance) modalInstance.hide();
                new bootstrap.Modal(document.getElementById("resultModal")).show();
                setTimeout(function() { location.reload(); }, 500);
            } catch (err) {
                alert("Error: " + (err.message || err));
            } finally {
                btn.disabled = false;
            }
        });
    }
})();

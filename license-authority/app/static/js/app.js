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
        if (isMachine) {
            maxActivations.value = "1";
            wrapMaxActivations.classList.add("d-none");
        } else {
            wrapMaxActivations.classList.remove("d-none");
        }
    }
    licenseType.addEventListener("change", toggleMachineFields);
    toggleMachineFields();

    function formatApiError(data, status) {
        if (!data) return "Error " + status;
        var detail = data.detail;
        if (Array.isArray(detail) && detail.length) {
            var first = detail[0];
            if (first && typeof first === "object") {
                var path = Array.isArray(first.loc) ? first.loc.join(".") : "";
                var msg = first.msg || JSON.stringify(first);
                return path ? (path + ": " + msg) : msg;
            }
            return detail.join(", ");
        }
        if (detail && typeof detail === "object") return JSON.stringify(detail);
        if (typeof detail === "string" && detail.trim()) return detail;
        if (typeof data.message === "string" && data.message.trim()) return data.message;
        return JSON.stringify(data);
    }

    form.addEventListener("submit", async function(e) {
        e.preventDefault();
        var btn = document.getElementById("btnCreate");
        btn.disabled = true;
        var fd = new FormData(form);
        var productId = (fd.get("feature_product_id") || "").toString().trim();
        var selectedCapabilities = fd.getAll("feature_funcionality")
            .map(function(v) { return v.toString().trim(); })
            .filter(Boolean);
        if (!productId) {
            alert("Debes indicar el ID de producto.");
            btn.disabled = false;
            return;
        }
        if (!selectedCapabilities.length) {
            alert("Debes seleccionar al menos una funcionalidad.");
            btn.disabled = false;
            return;
        }
        var machineLock = (fd.get("machine_lock") || "").toString().trim();
        var machineId = (fd.get("machine_id") || "").toString().trim();
        if (!machineId) {
            alert("Debes indicar Machine ID.");
            btn.disabled = false;
            return;
        }
        if (licenseType.value === "machine" && !machineLock && !machineId) {
            alert("Para licencias machine debes indicar Machine lock o Machine ID.");
            btn.disabled = false;
            return;
        }
        var features = [{
            id: productId,
            version: "2026.1",
            funcionality: selectedCapabilities.join(",")
        }];
        var body = {
            company: fd.get("company").toString().trim(),
            license_type: fd.get("license_type"),
            max_activations: parseInt(fd.get("max_activations") || "1", 10),
            duration_days: parseInt(fd.get("duration_days") || "365", 10),
            features: features
        };
        if (licenseType.value === "machine") {
            body.machine_lock = machineLock || null;
        } else {
            body.machine_lock = null;
        }
        body.machine_id = machineId || null;
        try {
            var r = await fetch("/create", {
                method: "POST",
                credentials: "same-origin",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (r.status === 401) { window.location.href = "/login"; return; }
            var data = {};
            var isJson = (r.headers.get("content-type") || "").indexOf("application/json") !== -1;
            if (isJson) data = await r.json();
            if (!r.ok) throw new Error(formatApiError(data, r.status));
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

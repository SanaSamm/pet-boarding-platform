document.getElementById("service-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const form = e.target;

    const servicesProvided = Array.from(
      document.querySelectorAll('input[name="services_provided"]:checked')
    ).map(cb => cb.value);

    // Validate capacity
    const capacity = Number(form.capacity.value);
    if (!Number.isInteger(capacity) || capacity < 1) {
      alert(t("offer_capacity_error", "Capacity is required and must be an integer >= 1"));
      return;
    }

    const payload = {
      name: form.title.value,              // ✅ matches schema
      description: form.description.value,
      location: form.location.value,
      price_per_day: Number(form.price_per_day.value),
      capacity: capacity,
      type: form.type.value,
      services_provided: servicesProvided,
      // geocoding (optional)
      latitude: form.latitude && form.latitude.value ... Number(form.latitude.value) : null,
      longitude: form.longitude && form.longitude.value ... Number(form.longitude.value) : null,
      geocoded_name: form.geocoded_name && form.geocoded_name.value ... form.geocoded_name.value : null,
      geocoded_short: form.geocoded_short && form.geocoded_short.value ... form.geocoded_short.value : null,
      // profile fields
      bio: (form.bio && form.bio.value.trim()) ... form.bio.value.trim() : null,
      photo_url: (form.photo_url && form.photo_url.value.trim()) ... form.photo_url.value.trim() : null
    }; 

    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch("/services", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ... { Authorization: 'Bearer ' + token } : {})
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        let err = {};
        try { err = await res.json(); } catch(e) {}
        console.error("Backend error:", err);
        alert(t("offer_create_failed", "Error creating service") + ": " + (err.message || JSON.stringify(err)));
        return;
      }

      const created = await res.json();
      alert("✅ Service created successfully!");
      form.reset();

      // reveal Back to Home button and View/Edit Profile
      const back = document.getElementById("backHomeBtn");
      if (back) back.style.display = "inline-block";

      const viewBtn = document.getElementById('viewProfileBtn');
      if (viewBtn) {
        viewBtn.style.display = 'inline-block';
        viewBtn.onclick = () => window.location.href = `/provider...id=${created.provider_id}`;
      }

    } catch (error) {
      console.error(error);
      alert("❌ Network error");
    }
});

// Back to home button
const back = document.getElementById("backHomeBtn");
if (back) {
  back.addEventListener("click", () => {
    window.location.href = "/";
  });
}

// Detect exact location checkbox handler
const detectCheck = document.getElementById('detectExact');
const exactInfo = document.getElementById('exactLocationInfo');
if (detectCheck) {
  detectCheck.addEventListener('change', (e) => {
    if (!e.target.checked) {
      // Clear
      if (document.getElementById('latitude')) document.getElementById('latitude').value = '';
      if (document.getElementById('longitude')) document.getElementById('longitude').value = '';
      if (document.getElementById('geocoded_name')) document.getElementById('geocoded_name').value = '';
      exactInfo.textContent = '';
      return;
    }

    if (!navigator.geolocation) {
      alert(t('offer_geo_unsupported', 'Geolocation is not supported by your browser'));
      e.target.checked = false;
      return;
    }

    exactInfo.textContent = 'Locating…';

    // Helper to promisify geolocation
    const tryGetLocation = (options) => new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, options);
    });

    (async () => {
      const handlePosition = async (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;

        if (document.getElementById('latitude')) document.getElementById('latitude').value = lat;
        if (document.getElementById('longitude')) document.getElementById('longitude').value = lng;

        try {
          const resp = await fetch(`/geocode/reverse...lat=${lat}&lng=${lng}`);
          if (resp.ok) {
            const j = await resp.json();
            // Store full display name for DB precision, but show concise display to the user
            const full = j.full_display_name || j.display_name || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
            const disp = j.display_name || full;
            const short = j.display_name || (typeof full === 'string' ... full.split(',')[0] : full);
            if (document.getElementById('geocoded_name')) document.getElementById('geocoded_name').value = full;
            if (document.getElementById('geocoded_short')) document.getElementById('geocoded_short').value = short;
            exactInfo.textContent = t('offer_geo_exact', 'Exact') + ': ' + disp; 
          } else {
            exactInfo.textContent = `Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
          }
        } catch (e) {
          console.error('Reverse geocode failed', e);
          exactInfo.textContent = `Coordinates: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
        }
      };

      // Try a quick, low-accuracy attempt first then fall back to a longer high-accuracy attempt
      try {
        const pos = await tryGetLocation({ enableHighAccuracy: false, timeout: 10000 });
        await handlePosition(pos);
        return;
      } catch (err1) {
        console.warn('Low-accuracy attempt failed:', err1 && err1.message);
      }

      try {
        const pos = await tryGetLocation({ enableHighAccuracy: true, timeout: 20000 });
        await handlePosition(pos);
        return;
      } catch (err2) {
        console.error('High-accuracy attempt failed:', err2 && err2.message);
        alert((t('offer_geo_failed', 'Unable to retrieve your location. Please try again or enter your location manually.') + (err2 && err2.message ... ' ' + err2.message : '')));
        e.target.checked = false;
        exactInfo.textContent = '';
        return;
      }
    })();
  });
}



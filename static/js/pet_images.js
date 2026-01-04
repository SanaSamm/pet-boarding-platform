async function fetchDogImageUrl() {
  const res = await fetch('https://dog.ceo/api/breeds/image/random');
  if (!res.ok) return null;
  const data = await res.json();
  return data && data.message ? data.message : null;
}

async function fetchCatImageUrl() {
  const res = await fetch('https://api.thecatapi.com/v1/images/search');
  if (!res.ok) return null;
  const data = await res.json();
  if (Array.isArray(data) && data.length && data[0].url) return data[0].url;
  return null;
}

async function loadRandomPetImage(imgEl) {
  if (!imgEl) return;
  try {
    const url = await fetchDogImageUrl();
    if (url) {
      imgEl.src = url;
      return;
    }
  } catch (e) {
    // ignore and try cat
  }
  try {
    const catUrl = await fetchCatImageUrl();
    if (catUrl) {
      imgEl.src = catUrl;
    }
  } catch (e) {
    // ignore, keep existing src
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const imgs = document.querySelectorAll('[data-random-pet]');
  imgs.forEach((img) => loadRandomPetImage(img));
});

const form = document.getElementById('compareForm');
const resultsDiv = document.getElementById('results');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  resultsDiv.innerHTML = '<p>Loading comparison...</p>';

  const url1 = document.getElementById('url1').value.trim();
  const url2 = document.getElementById('url2').value.trim();

  try {
    const response = await fetch('https://feature-compare-i8tq.onrender.com', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url1, url2 })
    });

    const data = await response.json();
    if (data.error) {
      resultsDiv.innerHTML = `<p class="error">${data.error}</p>`;
      return;
    }

    resultsDiv.innerHTML = '';
    data.comparison.forEach(product => {
      const productHTML = `
        <div class="product-card">
          <h2>${product.title}</h2>
          <p><strong>Source:</strong> ${product.source}</p>
          <p><strong>Price:</strong> ${product.price}</p>
          <p><strong>Description:</strong> ${product.description}</p>
          <p><strong>URL:</strong> <a href="${product.url}" target="_blank">${product.url}</a></p>
          <p><strong>Key Features:</strong></p>
          <ul>${product.features.map(f => `<li>${f}</li>`).join('')}</ul>
        </div>
      `;
      resultsDiv.innerHTML += productHTML;
    });
  } catch (err) {
    resultsDiv.innerHTML = `<p class="error">Failed to fetch comparison. Please try again.</p>`;
    console.error(err);
  }

});

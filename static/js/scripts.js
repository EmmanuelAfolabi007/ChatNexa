document.addEventListener('DOMContentLoaded', () => {
    console.log('JavaScript loaded!');
});

document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const searchQueryInput = document.getElementById('search-query');
    const searchResultsContainer = document.getElementById('search-results');

    searchForm.addEventListener('submit', async (event) => {
        event.preventDefault();  // Prevent form submission

        const searchQuery = searchQueryInput.value.trim();

        if (searchQuery.length === 0) {
            return;  // Do nothing if the search query is empty
        }

        try {
            const response = await fetch(`/search?q=${encodeURIComponent(searchQuery)}`);
            const searchData = await response.json();
            displaySearchResults(searchData);
        } catch (error) {
            console.error('Error fetching search results:', error);
        }
    });

    function displaySearchResults(results) {
        // Clear previous search results
        searchResultsContainer.innerHTML = '';

        if (results.length === 0) {
            searchResultsContainer.textContent = 'No results found.';
            return;
        }

        // Display search results
        results.forEach(result => {
            const resultElement = document.createElement('div');
            resultElement.textContent = `${result.type}: ${result.name || result.title}`;
            searchResultsContainer.appendChild(resultElement);
        });
    }
});

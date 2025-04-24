const fileInput = document.getElementById('jsonFile');
const outputDiv = document.getElementById('output');
const controlsDiv = document.getElementById('controls');
const entitySetSelector = document.getElementById('entitySetSelector');

let currentJsonData = null; // Store the loaded JSON data

// Simple color mapping (can be expanded)
// CSS classes are generated as 'entity-' + label.replace(/ /g, '-')
const labelToClassSuffix = (label) => {
    return label.replace(/ /g, '-');
}

fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) {
        outputDiv.innerHTML = '<p>No file selected.</p>';
        controlsDiv.style.display = 'none'; // Hide controls
        currentJsonData = null;
        return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
        try {
            currentJsonData = JSON.parse(e.target.result);
            populateEntitySetSelector(currentJsonData);
            // Display the first available entity set by default
            if (entitySetSelector.options.length > 0) {
                entitySetSelector.selectedIndex = 0;
                displayHighlightedText(currentJsonData, entitySetSelector.value);
                controlsDiv.style.display = 'block'; // Show controls
            } else {
                outputDiv.innerHTML = '<p>No entity sets found in the JSON.</p>';
                controlsDiv.style.display = 'none'; // Hide controls
            }
        } catch (error) {
            console.error("Error parsing JSON:", error);
            outputDiv.innerHTML = `<p style="color: red;">Error parsing JSON file: ${error.message}</p>`;
            controlsDiv.style.display = 'none'; // Hide controls
            currentJsonData = null;
        }
    };

    reader.onerror = (e) => {
        console.error("Error reading file:", e);
        outputDiv.innerHTML = '<p style="color: red;">Error reading file.</p>';
        controlsDiv.style.display = 'none'; // Hide controls
        currentJsonData = null;
    };

    reader.readAsText(file);
});

entitySetSelector.addEventListener('change', () => {
    if (currentJsonData) {
        displayHighlightedText(currentJsonData, entitySetSelector.value);
    }
});

function populateEntitySetSelector(data) {
    entitySetSelector.innerHTML = ''; // Clear previous options
    if (data && data.entities) {
        const entitySetKeys = Object.keys(data.entities);
        if (entitySetKeys.length > 0) {
            entitySetKeys.forEach(key => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key;
                entitySetSelector.appendChild(option);
            });
        } else {
            const option = document.createElement('option');
            option.textContent = "No entity sets found";
            option.disabled = true;
            entitySetSelector.appendChild(option);
        }
    } else {
        const option = document.createElement('option');
        option.textContent = "No 'entities' key found";
        option.disabled = true;
        entitySetSelector.appendChild(option);
    }
}

function findMatchingChunkSetKey(data, selectedEntitySetKey) {
    if (!data || !data.chunks || !selectedEntitySetKey) return null;

    // Extract chunk size from the entity key (assuming format provider_model_chunksize)
    const parts = selectedEntitySetKey.split('_');
    const chunkSize = parts[parts.length - 1]; // Get the last part

    if (!chunkSize || isNaN(parseInt(chunkSize))) return null; // Invalid chunk size in key

    // Find a chunk key ending with _chunkSize
    for (const key in data.chunks) {
        if (key.endsWith(`_${chunkSize}`)) {
            return key;
        }
    }
    return null; // No matching chunk set found
}

function displayHighlightedText(data, selectedEntitySetKey) {
    outputDiv.innerHTML = ''; // Clear previous output

    if (!selectedEntitySetKey || !data.entities || !data.entities[selectedEntitySetKey]) {
        outputDiv.innerHTML = '<p style="color: orange;">Selected entity set not found.</p>';
        return;
    }

    // Find the corresponding chunk set based on the chunk size in the entity key
    const chunkSetKey = findMatchingChunkSetKey(data, selectedEntitySetKey);

    if (!chunkSetKey || !data.chunks[chunkSetKey] || !data.chunks[chunkSetKey].chunks) {
        outputDiv.innerHTML = `<p style="color: orange;">Could not find a matching chunk set for entity set '${selectedEntitySetKey}'. Expected chunk key ending with '_${selectedEntitySetKey.split('_').pop()}'.</p>`;
        return;
    }

    const chunks = data.chunks[chunkSetKey].chunks;
    const allEntities = data.entities[selectedEntitySetKey].entities || [];

    // Group entities by chunk number for easier processing
    const entitiesByChunk = {};
    allEntities.forEach(entity => {
        const chunkNum = entity.chunk_number;
        if (!entitiesByChunk[chunkNum]) {
            entitiesByChunk[chunkNum] = [];
        }
        entitiesByChunk[chunkNum].push(entity);
    });

    // Sort entities within each chunk by start index (descending) for safe insertion
    for (const chunkNum in entitiesByChunk) {
        entitiesByChunk[chunkNum].sort((a, b) => b.start - a.start);
    }

    // Process each chunk
    chunks.forEach((chunk, index) => {
        let chunkText = chunk.text;
        const chunkNum = index + 1; // chunk_number is 1-based
        const chunkEntities = entitiesByChunk[chunkNum] || [];

        // Insert entity spans into the text
        chunkEntities.forEach(entity => {
            const start = entity.start;
            const end = entity.end;
            const label = entity.label;
            const score = entity.score.toFixed(2);
            // Escape HTML characters in the original text to prevent rendering issues
            const originalText = chunkText.substring(start, end)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
            const classSuffix = labelToClassSuffix(label) || 'DEFAULT';

            const span = `<span class="entity entity-${classSuffix}" title="${label} (${score})" data-label="${label}">${originalText}</span>`;

            // Insert the span by replacing the original text portion
            chunkText = chunkText.substring(0, start) + span + chunkText.substring(end);
        });

        // Add chunk separator and text to output
        if (index > 0) {
            const separator = document.createElement('div');
            separator.className = 'chunk-separator';
            separator.textContent = `--- Chunk ${chunkNum} (Pos: ${chunk.metadata?.position || chunkNum}) ---`;
            outputDiv.appendChild(separator);
        } else {
            const separator = document.createElement('div');
            separator.className = 'chunk-separator';
            separator.textContent = `--- Chunk ${chunkNum} (Pos: ${chunk.metadata?.position || chunkNum}) ---`;
            separator.style.borderTop = 'none'; // No border for the first one
            separator.style.margin = '0 0 20px 0';
            outputDiv.appendChild(separator);
        }
        // Use innerHTML to render the spans correctly
        const textElement = document.createElement('div');
        textElement.innerHTML = chunkText;
        outputDiv.appendChild(textElement);
    });

    if (chunks.length === 0) {
        outputDiv.innerHTML = '<p>No chunks found in the data for the selected set.</p>';
    }
}

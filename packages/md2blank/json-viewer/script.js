const fileInput = document.getElementById('jsonFile');
const outputDiv = document.getElementById('output');
const controlsDiv = document.getElementById('controls');
const entitySetSelector = document.getElementById('entitySetSelector');
const statsCard = document.getElementById('statsCard');
const statsContent = document.getElementById('statsContent');


let currentJsonData = null; // Store the loaded JSON data

// ... existing labelToClassSuffix function ...
const labelToClassSuffix = (label) => {
    // Sanitize label for CSS class: replace spaces, slashes, etc. with hyphens
    return label.replace(/[\s/]+/g, '-');
}


fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) {
        outputDiv.innerHTML = '<p>No file selected.</p>';
        controlsDiv.style.display = 'none'; // Hide controls
        statsCard.style.display = 'none'; // Hide stats card
        currentJsonData = null;
        return;
    }

    const reader = new FileReader();

    reader.onload = (e) => {
        try {
            currentJsonData = JSON.parse(e.target.result);
            populateEntitySetSelector(currentJsonData);
            // Display the first available entity set by default
            if (entitySetSelector.options.length > 0 && !entitySetSelector.options[0].disabled) {
                entitySetSelector.selectedIndex = 0;
                displayHighlightedText(currentJsonData, entitySetSelector.value);
                controlsDiv.style.display = 'block'; // Show controls
                statsCard.style.display = 'block'; // Show stats card
            } else {
                 outputDiv.innerHTML = '<p>No processable entity sets found in the JSON.</p>';
                 controlsDiv.style.display = 'none'; // Hide controls
                 statsCard.style.display = 'none'; // Hide stats card
            }
        } catch (error) {
            console.error("Error parsing JSON:", error);
            outputDiv.innerHTML = `<p style="color: red;">Error parsing JSON file: ${error.message}</p>`;
            controlsDiv.style.display = 'none'; // Hide controls
            statsCard.style.display = 'none'; // Hide stats card
            currentJsonData = null;
        }
    };

    reader.onerror = (e) => {
        console.error("Error reading file:", e);
        outputDiv.innerHTML = '<p style="color: red;">Error reading file.</p>';
        controlsDiv.style.display = 'none'; // Hide controls
        statsCard.style.display = 'none'; // Hide stats card
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
    // ... existing code ...
    entitySetSelector.innerHTML = ''; // Clear previous options
    let foundSelectable = false;
    if (data && data.entities) {
        const entitySetKeys = Object.keys(data.entities);
        if (entitySetKeys.length > 0) {
            entitySetKeys.forEach(key => {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = key;
                entitySetSelector.appendChild(option);
                foundSelectable = true;
            });
        }
    }

    if (!foundSelectable) {
         const option = document.createElement('option');
         option.textContent = "No entity sets found";
         option.disabled = true;
         entitySetSelector.appendChild(option);
    }
}


function findMatchingChunkSetKey(data, selectedEntitySetKey) {
    // ... existing code ...
    if (!data || !data.chunks || !selectedEntitySetKey) return null;

    // Extract chunk size from the entity key (assuming format provider_model_chunksize)
    const parts = selectedEntitySetKey.split('_');
    // Handle cases where model name might have underscores
    const potentialChunkSize = parts[parts.length - 1];

    if (!potentialChunkSize || isNaN(parseInt(potentialChunkSize))) {
        console.warn(`Could not reliably determine chunk size from entity key: ${selectedEntitySetKey}`);
        // Fallback: Try to find the first chunk set key available
        const firstChunkKey = Object.keys(data.chunks)[0];
        return firstChunkKey || null;
    }
    const chunkSize = potentialChunkSize;


    // Find a chunk key ending with _chunkSize
    for (const key in data.chunks) {
        if (key.endsWith(`_${chunkSize}`)) {
            return key;
        }
    }
    console.warn(`No chunk key found ending with _${chunkSize}. Falling back to first available chunk key.`);
    // Fallback if specific chunk size match fails
    const firstChunkKey = Object.keys(data.chunks)[0];
    return firstChunkKey || null;
}

function calculateAndDisplayStats(entities) {
    // Find the table body within the statsContent div
    const statsTableBody = statsContent.querySelector('table tbody');
    if (!statsTableBody) {
        console.error("Stats table body not found!");
        statsContent.innerHTML = '<p>Error: Stats table structure missing.</p>';
        return;
    }
    statsTableBody.innerHTML = ''; // Clear previous stats rows

    if (!entities || entities.length === 0) {
        const row = statsTableBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 2; // Span across both columns
        cell.textContent = 'No entities found for this set.';
        return;
    }

    const entitiesByType = {};
    const examplesByType = {};

    entities.forEach(entity => {
        // Count by Type
        entitiesByType[entity.label] = (entitiesByType[entity.label] || 0) + 1;

        // Collect examples by Type
        if (!examplesByType[entity.label]) {
            examplesByType[entity.label] = new Set(); // Use a Set to avoid duplicate examples
        }
        // Limit the number of examples stored per type for performance/display reasons
        if (examplesByType[entity.label].size < 5) {
             examplesByType[entity.label].add(entity.text);
        }
    });

    // Sort types alphabetically for consistent order
    const sortedTypes = Object.keys(entitiesByType).sort();

    // Build table rows
    sortedTypes.forEach(type => {
        const count = entitiesByType[type];
        const examples = Array.from(examplesByType[type] || []).join(', '); // Get examples as comma-separated string
        const row = statsTableBody.insertRow();

        const typeCell = row.insertCell();
        typeCell.textContent = `${type} (${count})`; // Show count with type

        const examplesCell = row.insertCell();
        examplesCell.textContent = examples || '-'; // Show examples or a dash
        examplesCell.title = examples; // Add full list as tooltip if needed
    });
}

function displayHighlightedText(data, selectedEntitySetKey) {
    // ... existing code ...
    // Clear previous output - Keep this
    outputDiv.innerHTML = '';
    // Reset stats display - We modify the table body directly now, so clearing the parent isn't strictly needed, but good practice
    const statsTableBody = statsContent.querySelector('table tbody');
    if (statsTableBody) {
        statsTableBody.innerHTML = '<tr><td colspan="2">Loading stats...</td></tr>';
    } else {
        statsContent.innerHTML = '<p>Loading stats...</p>'; // Fallback
    }


    if (!selectedEntitySetKey || !data.entities || !data.entities[selectedEntitySetKey]) {
        outputDiv.innerHTML = '<p style="color: orange;">Selected entity set not found.</p>';
        // Update stats table with error
        if (statsTableBody) {
             statsTableBody.innerHTML = '<tr><td colspan="2" style="color: orange;">Selected entity set not found.</td></tr>';
        } else {
            statsContent.innerHTML = '<p style="color: orange;">Selected entity set not found.</p>'; // Fallback
        }
        statsCard.style.display = 'block'; // Keep stats card visible to show the error
        return;
    }

    // Find the corresponding chunk set based on the chunk size in the entity key
    const chunkSetKey = findMatchingChunkSetKey(data, selectedEntitySetKey);

    if (!chunkSetKey || !data.chunks[chunkSetKey] || !data.chunks[chunkSetKey].chunks) {
        const potentialChunkSize = selectedEntitySetKey.split('_').pop();
        const errorMsg = `Could not find a matching chunk set for entity set '${selectedEntitySetKey}'. Expected chunk key ending with '_${potentialChunkSize}'.`;
        const errorHtml = `<p style="color: orange;">${errorMsg}</p>`;
        outputDiv.innerHTML = errorHtml;
         // Update stats table with error
        if (statsTableBody) {
             statsTableBody.innerHTML = `<tr><td colspan="2" style="color: orange;">${errorMsg}</td></tr>`;
        } else {
            statsContent.innerHTML = errorHtml; // Fallback
        }
        statsCard.style.display = 'block'; // Keep stats card visible to show the error
        return;
    }

    const chunks = data.chunks[chunkSetKey].chunks;
    const allEntities = data.entities[selectedEntitySetKey].entities || [];

    // Calculate and display stats *before* processing chunks for display
    calculateAndDisplayStats(allEntities); // This now populates the table body
    statsCard.style.display = 'block'; // Ensure stats card is visible


    // ... existing entity grouping and sorting ...
    const entitiesByChunk = {};
    allEntities.forEach(entity => {
        const chunkNum = entity.chunk_number;
        if (!entitiesByChunk[chunkNum]) {
            entitiesByChunk[chunkNum] = [];
        }
        entitiesByChunk[chunkNum].push(entity);
    });
    for (const chunkNum in entitiesByChunk) {
        entitiesByChunk[chunkNum].sort((a, b) => b.start - a.start);
    }


    // ... existing chunk processing and highlighting logic ...
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
        // const chunkElement = document.createElement('div'); // Not needed directly
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
        // IMPORTANT: Use innerHTML carefully. We escaped the originalText before wrapping it in a span.
        textElement.innerHTML = chunkText;
        outputDiv.appendChild(textElement);

    });

    if (chunks.length === 0 && allEntities.length > 0) { // Check if chunks are empty but entities exist
         outputDiv.innerHTML = '<p>Entities found, but no corresponding chunks were found in the data for the selected set.</p>';
         // Stats are already displayed correctly
    } else if (chunks.length === 0 && allEntities.length === 0) {
         outputDiv.innerHTML = '<p>No chunks or entities found in the data for the selected set.</p>';
         // Stats already show "No entities found"
    }
}

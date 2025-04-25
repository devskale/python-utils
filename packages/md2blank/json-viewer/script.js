const fileInput = document.getElementById('jsonFile');
const outputDiv = document.getElementById('output');
const controlsDiv = document.getElementById('controls');
const entitySetSelector = document.getElementById('entitySetSelector');
const statsCard = document.getElementById('statsCard');
const statsContent = document.getElementById('statsContent');

let currentJsonData = null; // Store the loaded JSON data

// --- Color Generation Helpers ---

/** Simple hash function for a string */
function hashCode(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash |= 0; // Convert to 32bit integer
    }
    return Math.abs(hash);
}

/** Convert an integer hash to an HSL color string */
function intToHSL(i) {
    const hue = i % 360; // Cycle through hues
    const saturation = 70; // Keep saturation constant and vibrant
    const lightness = 80; // Keep lightness relatively light for backgrounds
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/** Convert HSL color value to RGB. h, s, and l are contained in [0..1] and return r, g, and b in [0..255]. */
function hslToRgb(h, s, l){
    let r, g, b;
    h /= 360; // Convert hue to range 0-1

    if(s == 0){
        r = g = b = l; // achromatic
    } else {
        const hue2rgb = (p, q, t) => {
            if(t < 0) t += 1;
            if(t > 1) t -= 1;
            if(t < 1/6) return p + (q - p) * 6 * t;
            if(t < 1/2) return q;
            if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        }
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }
    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

/** Get contrasting text color (black or white) based on HSL background */
function getContrastColor(hslString) {
    const match = hslString.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
    if (!match) return '#000000'; // Default to black if parse fails
    const h = parseInt(match[1]);
    const s = parseInt(match[2]) / 100;
    const l = parseInt(match[3]) / 100;

    const rgb = hslToRgb(h, s, l);
    const yiq = ((rgb[0] * 299) + (rgb[1] * 587) + (rgb[2] * 114)) / 1000;
    return (yiq >= 128) ? '#000000' : '#ffffff'; // Black for light backgrounds, white for dark
}

/** Adjust the lightness of an HSL color string */
function adjustHSLColor(hslString, lightnessAdjustmentPercent) {
    const match = hslString.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
    if (!match) return hslString; // Return original if parse fails
    const h = parseInt(match[1]);
    const s = parseInt(match[2]);
    let l = parseInt(match[3]);
    l = Math.max(0, Math.min(100, l + lightnessAdjustmentPercent)); // Adjust and clamp lightness
    return `hsl(${h}, ${s}%, ${l}%)`;
}

// --- End Color Generation Helpers ---

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
    // Define escapeHtml function at the beginning of the scope
    const escapeHtml = (unsafe) => {
        return unsafe
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
    }

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
    let allEntities = data.entities[selectedEntitySetKey].entities || []; // Use let to allow reassignment

    // Calculate and display stats *before* processing chunks for display
    calculateAndDisplayStats(allEntities); // This now populates the table body
    statsCard.style.display = 'block'; // Ensure stats card is visible

    // Filter out exact duplicate entities before further processing
    const uniqueEntityKeys = new Set();
    allEntities = allEntities.filter(entity => {
        // Create a unique key for each entity based on relevant properties
        const key = `${entity.chunk_number}-${entity.start}-${entity.end}-${entity.label}`;
        if (uniqueEntityKeys.has(key)) {
            // If key already exists, it's a duplicate
            console.warn(`Filtering duplicate entity: ${JSON.stringify(entity)}`);
            return false; 
        } else {
            // If key is new, add it to the set and keep the entity
            uniqueEntityKeys.add(key);
            return true;
        }
    });

    // Group entities by chunk number
    const entitiesByChunk = {};
    allEntities.forEach(entity => {
        // Ensure indices are numbers and valid, skip if not
        if (typeof entity.start !== 'number' || typeof entity.end !== 'number' || entity.start < 0 || entity.end < 0 || entity.start > entity.end) {
             console.warn(`Invalid indices for entity, skipping: ${JSON.stringify(entity)}`);
             return;
        }
        const chunkNum = entity.chunk_number;
        if (!entitiesByChunk[chunkNum]) {
            entitiesByChunk[chunkNum] = [];
        }
        entitiesByChunk[chunkNum].push(entity);
    });

    // Sort entities within each chunk by start index (ascending)
    for (const chunkNum in entitiesByChunk) {
        entitiesByChunk[chunkNum].sort((a, b) => a.start - b.start);
    }

    // Process each chunk and build HTML output segment by segment
    chunks.forEach((chunk, index) => {
        const originalChunkText = chunk.text; // Use the original text
        const chunkNum = index + 1; // chunk_number is 1-based
        const chunkEntities = entitiesByChunk[chunkNum] || [];
        let highlightedHtml = '';
        let lastIndex = 0;

        // Iterate through sorted entities for the current chunk
        chunkEntities.forEach(entity => {
            const start = entity.start;
            const end = entity.end;

            // Check for invalid indices relative to the original chunk text length
             if (start < lastIndex || end > originalChunkText.length) {
                 console.warn(`Entity indices [${start}, ${end}] out of bounds or overlapping incorrectly for chunk ${chunkNum}. Skipping entity: ${JSON.stringify(entity)}`);
                 return; // Skip this entity
             }

            const label = entity.label;
            const scoreValue = (typeof entity.score === 'number') ? entity.score.toFixed(2) : 'N/A';
            const titleText = (typeof entity.score === 'number') ? `${label} (${scoreValue})` : label;

            // --- Generate Colors ---
            const labelHash = hashCode(label);
            const bgColor = intToHSL(labelHash);
            const textColor = getContrastColor(bgColor);
            const borderColor = adjustHSLColor(bgColor, -20); // Slightly darker border

            // Append the text segment *before* the current entity
            highlightedHtml += escapeHtml(originalChunkText.substring(lastIndex, start));

            // Append the highlighted entity span with inline styles and inner label span
            const entityText = escapeHtml(originalChunkText.substring(start, end));
            
            // Style for the outer span (entity text)
            const mainSpanStyle = `background-color: ${bgColor}; border-color: ${borderColor}; color: ${textColor};`;
            
            // Style for the label - make it distinct with its own background
            // Use a darker background for the label to make it stand out
            const labelBgColor = adjustHSLColor(bgColor, -10); // Slightly darker background
            const labelSpanStyle = `background-color: ${labelBgColor}; border-color: ${borderColor}; color: ${textColor};`;

            // Construct the HTML with an inner span for the pill-shaped label
            const span = '<span class="entity" title="' + titleText + '" style="' + mainSpanStyle + '">' +
                         entityText.trim() +
                         '<span class="entity-label" style="' + labelSpanStyle + '">' +
                         escapeHtml(label).trim() +
                         '</span></span>';
            highlightedHtml += span;

            // Update the last index processed
            lastIndex = end;
        });

        // Append any remaining text *after* the last entity
        highlightedHtml += escapeHtml(originalChunkText.substring(lastIndex));

        // Add chunk separator
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

        // Add the constructed HTML for the chunk
        const textElement = document.createElement('div');
        textElement.innerHTML = highlightedHtml; // Use the correctly built HTML
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

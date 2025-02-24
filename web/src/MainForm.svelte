<script>
  import { onMount } from "svelte";
  import defaultWorkflow from "./workflows/flux_unet.json";
  import unetWorkflow from "./workflows/flux_unet_lora.json";

  // props
  export let useCkptModels = false;
  export let serverAddress = "";
  export let positivePrompt;
  export let selectedModel;
  export let selectedSize;
  export let steps;
  export let cfg;

  // variables
  let clientId;
  let ws;
  let imageUrl = "";
  let status = "Ready";
  let promptId;
  let history = [];
  let currentPage = 0;
  let maxPageIndex = 0;
  let isGenerating = false;
  let generationCooldown = false;
  let currentWorkflow = defaultWorkflow;
  let selectedImage = null;
  let showLightbox = false;

  // Form bindings
  //let negativePrompt = "lowres, bad anatomy...";
  let seed = Math.floor(Math.random() * 1000000000);
  let loadingModels = true;
  let modelOptions = [];

  let sizeOptions = [
    { label: "1920x1080", width: 1920, height: 1080 },
    { label: "1024x1024", width: 1024, height: 1024 },
    { label: "720x1280", width: 720, height: 1280 },
    { label: "512x512", width: 512, height: 512 },
    { label: "800x600", width: 800, height: 600 },
  ];

  onMount(async () => {
    if (!serverAddress) return;
    console.log("Server address:", serverAddress);
    clientId = crypto.randomUUID();
    try {
      const response = await fetch(`${serverAddress}/object_info`);
      const data = await response.json();
      let models = [];
      if (useCkptModels) {
        models = data.CheckpointLoaderSimple.input.required.ckpt_name[0];
      } else {
        models = data.UNETLoader.input.required.unet_name[0];
      }
      //const models = data.CheckpointLoaderSimple.input.required.ckpt_name[0];
      modelOptions = models;
    } catch (error) {
      console.error("Error loading models:", error);
      modelOptions = ["DefaultModel.safetensors"]; // Fallback
    } finally {
      loadingModels = false;
    }
    return () => {
      if (ws) {
        ws.close();
      }
    };
  });

  // Reactive statements
  $: if (serverAddress && useCkptModels !== undefined) {
    fetchModels();
  }
  $: {
    currentWorkflow = useCkptModels ? unetWorkflow : defaultWorkflow;
    if (useCkptModels) fetchModels(); // Force refresh when toggling
  }
  $: prevImages = history.length >= 1 ? history.slice(0, -1).reverse() : [];
  $: maxPageIndex = Math.ceil(prevImages.length / 3) - 1;

  // Handle previous img page navigation
  function handlePrevPage() {
    currentPage = Math.max(currentPage - 1, 0);
  }

  // Handle next img page navigation
  function handleNextPage() {
    currentPage = Math.min(currentPage + 1, maxPageIndex);
  }

  async function fetchModels() {
    if (!serverAddress) return;

    loadingModels = true;
    try {
      const response = await fetch(`${serverAddress}/object_info`);
      const data = await response.json();

      const modelPath = useCkptModels
        ? "CheckpointLoaderSimple.input.required.ckpt_name[0]"
        : "UNETLoader.input.required.unet_name[0]";

      if (!selectedModel) {
        selectedModel = useCkptModels
          ? data.CheckpointLoaderSimple.input.required.ckpt_name[0][0]
          : data.UNETLoader.input.required.unet_name[0][0];
      }

      modelOptions = getNestedProperty(data, modelPath) || [];
    } catch (error) {
      console.error("Error loading models:", error);
      modelOptions = ["DefaultModel.safetensors"];
    } finally {
      loadingModels = false;
    }
  }

  // Helper function to access nested properties
  function getNestedProperty(obj, path) {
    return path.split(".").reduce((acc, part) => {
      const arrayMatch = part.match(/(\w+)\[(\d+)\]/);
      if (arrayMatch) {
        const prop = arrayMatch[1];
        const index = parseInt(arrayMatch[2]);
        return acc && acc[prop] && acc[prop][index];
      }
      return acc && acc[part];
    }, obj);
  }

  async function generateImage(e) {
    e.preventDefault();
    if (generationCooldown) return;

    isGenerating = true;
    generationCooldown = true;
    status = "Generating...";

    try {
      // Prepare prompt
      const apiUrl = new URL(serverAddress);
      const prompt = structuredClone(currentWorkflow);
      const currentSeed = seed;

      // Update model loading node based on workflow
      if (useCkptModels) {
        prompt["30"].inputs.ckpt_name = selectedModel;
      } else {
        prompt["12"].inputs.unet_name = selectedModel;
      }

      prompt["6"].inputs.text = positivePrompt;
      //prompt["33"].inputs.text = negativePrompt;
      prompt["25"].inputs.noise_seed = seed;
      prompt["17"].inputs.steps = steps;
      prompt["27"].inputs.guidance = cfg;
      prompt["5"].inputs.width = selectedSize.split("x")[0];
      prompt["5"].inputs.height = selectedSize.split("x")[1];

      // Queue prompt
      const queueResponse = await fetch(`${apiUrl.origin}/prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, client_id: clientId }),
      });
      promptId = (await queueResponse.json()).prompt_id;

      // Determine connection method
      if (apiUrl.hostname === "localhost" || apiUrl.hostname === "127.0.0.1") {
        await waitForWebSocketCompletion(apiUrl);
      } else {
        await pollForCompletion(promptId, apiUrl);
      }

      // Fetch image data
      const historyResponse = await fetch(
        `${apiUrl.origin}/history/${promptId}`,
      );
      const apiHistory = await historyResponse.json();
      const imgData = apiHistory[promptId]?.outputs?.["9"]?.images?.[0];

      if (imgData && imgData.filename) {
        imageUrl = `${apiUrl.origin}/view?filename=${imgData.filename}&subfolder=${encodeURIComponent(
          imgData.subfolder,
        )}&type=${imgData.type}`;

        // Update history
        history = [
          ...history,
          {
            url: imageUrl,
            positivePrompt: positivePrompt,
            //negativePrompt: negativePrompt,
            seed: seed,
            steps: steps,
            cfg: cfg,
            size: selectedSize,
            timestamp: Date.now(),
          },
        ];
        isGenerating = false;
        generationCooldown = false;
        seed = Math.floor(Math.random() * 1000000000);
        status = "Ready";
      } else {
        throw new Error("Image data not found");
      }
    } catch (err) {
      status = `Error: ${err.message}`;
      isGenerating = false;

      // Re-enable after 5 seconds
      setTimeout(() => {
        generationCooldown = false;
      }, 5000);
    }
  }

  async function waitForWebSocketCompletion(apiUrl) {
    return new Promise((resolve, reject) => {
      const wsProtocol = apiUrl.protocol === "https:" ? "wss" : "ws";
      const wsUrl = `${wsProtocol}://${apiUrl.host}/ws?clientId=${clientId}`;

      ws = new WebSocket(wsUrl);

      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "executed" && msg.data.node === "9") {
          // Check SaveImage node
          ws.close();
          resolve();
        }
      };

      ws.onerror = reject;
    });
  }

  async function pollForCompletion(promptId, apiUrl) {
    let attempts = 0;
    const maxAttempts = 500; // 2-minute timeout

    while (attempts < maxAttempts) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      attempts++;

      try {
        const historyResponse = await fetch(
          `${apiUrl.origin}/history/${promptId}`,
        );
        const history = await historyResponse.json();
        if (history[promptId]?.outputs?.["9"]?.images?.[0]) {
          return;
        }
      } catch (err) {
        // Ignore polling errors
      }
    }
    throw new Error("Generation timed out");
  }

  function openLightbox(image) {
    selectedImage = image;
    showLightbox = true;
    document.body.classList.add("overflow-hidden");
  }

  function closeLightbox() {
    selectedImage = null;
    showLightbox = false;
    document.body.classList.remove("overflow-hidden");
  }

  function downloadImage(url) {
    const a = document.createElement("a");
    a.href = url;
    a.download = "generated_image.png";
    a.click();
  }
</script>

<main class="container mx-auto px-4 py-6">
  <form on:submit={generateImage} class="flex flex-col md:flex-row gap-6">
    <!-- Left Panel - Controls -->
    <div class="w-full md:w-1/2 space-y-6">
      <div class="card bg-base-100 shadow-xl p-6">
        <h2 class="text-xl font-bold mb-4">Generation Settings</h2>

        <!-- Server Address -->
        <div class="form-control">
          <label class="label" for="serverAddress">
            <span class="label-text font-semibold">Server: {serverAddress}</span
            >
          </label>
        </div>

        <!-- Model Selection -->
        <div class="form-control">
          <label class="label" for="modelSelection">
            <span class="label-text font-semibold">Model</span>
          </label>
          <select
            id="modelSelection"
            bind:value={selectedModel}
            class="select select-bordered w-full max-w-xs"
            disabled={loadingModels}
          >
            {#each modelOptions as model}
              <option value={model}>{model}</option>
            {/each}
          </select>
          {#if loadingModels}
            <span class="loading loading-spinner"></span>
          {/if}
        </div>

        <!-- Positive Prompt -->
        <div class="form-control">
          <label class="label" for="positive-prompt">
            <span class="label-text font-semibold">Positive Prompt</span>
          </label>
          <textarea
            id="positive-prompt"
            bind:value={positivePrompt}
            rows="4"
            class="textarea textarea-bordered textarea-lg w-full"
            placeholder="Describe what you want to generate..."
          />
        </div>

        <!-- Parameters Grid -->
        <div class="grid grid-cols-1 md:grid-cols-1 gap-4 mt-6">
          <div class="form-control">
            <label class="label" for="seed">
              <span class="label-text">Seed</span>
            </label>
            <input
              id="seed"
              type="number"
              bind:value={seed}
              class="input input-bordered w-full"
            />
          </div>

          <div class="form-control">
            <label class="label" for="steps">
              <span class="label-text">Steps ({steps})</span>
            </label>
            <input
              id="steps"
              type="range"
              bind:value={steps}
              min="1"
              max="50"
              class="range range-primary"
            />
          </div>

          <div class="form-control">
            <label class="label" for="cfg">
              <span class="label-text">CFG Scale ({cfg})</span>
            </label>
            <input
              id="cfg"
              type="range"
              bind:value={cfg}
              min="1"
              max="20"
              step="0.5"
              class="range range-secondary"
            />
          </div>

          <!-- Image Size -->
          <div class="form-control">
            <label class="label" for="imageSize">
              <span class="label-text font-semibold">Image Size</span>
            </label>
            <select
              id="imageSize"
              bind:value={selectedSize}
              class="select select-bordered w-full max-w-xs"
            >
              {#each sizeOptions as option}
                <option value={`${option.width}x${option.height}`}
                  >{option.label}</option
                >
              {/each}
            </select>
          </div>
        </div>

        <!-- Generate Button -->
        <div class="mt-6">
          <button
            type="submit"
            class="btn btn-primary w-full"
            disabled={generationCooldown || isGenerating}
          >
            {#if isGenerating}
              <span class="loading loading-spinner"></span>
              Generating
            {:else if generationCooldown}
              Cooling Down...
            {:else}
              Generate Image
            {/if}
          </button>
        </div>
      </div>
    </div>

    <!-- Right Panel - Output -->
    <div class="w-full md:w-1/2">
      <div class="card bg-base-100 shadow-xl p-6 h-full">
        <div class="flex flex-col h-full">
          <!-- Status Indicator -->
          <div class="badge badge-lg badge-ghost mb-4 self-end">
            {status}
          </div>

          <!-- Image Preview -->
          {#if imageUrl}
            <figure
              class="flex-1 bg-neutral rounded-box overflow-hidden relative cursor-zoom-in"
            >
              <img
                src={imageUrl}
                alt="Generated"
                class="w-full h-auto object-contain"
                on:click={() => openLightbox(history[history.length - 1])}
              />
            </figure>

            {#if prevImages.length > 0}
              <div class="mt-4">
                <div class="flex items-center justify-between">
                  <!-- Left Arrow -->
                  <button
                    on:click={handlePrevPage}
                    class="btn btn-circle"
                    disabled={currentPage === 0}
                  >
                    ❰
                  </button>

                  <!-- Thumbnails -->
                  <div class="flex gap-4 overflow-hidden">
                    {#each prevImages.slice(currentPage * 3, currentPage * 3 + 3) as image}
                      <!-- svelte-ignore a11y-click-events-have-key-events -->
                      <div
                        class="tooltip cursor-pointer"
                        data-tip={image.positivePrompt}
                        on:click={() => openLightbox(image)}
                      >
                        <!-- svelte-ignore a11y-missing-attribute -->
                        <img
                          src={image.url}
                          class="h-20 w-20 object-cover rounded-box border-2 border-base-300"
                        />
                      </div>
                    {/each}
                  </div>

                  <!-- Right Arrow -->
                  <button
                    on:click={handleNextPage}
                    class="btn btn-circle"
                    disabled={currentPage === maxPageIndex}
                  >
                    ❱
                  </button>
                </div>
              </div>
            {/if}

            <!-- Metadata Collapse -->
            <div class="collapse collapse-arrow mt-4">
              <input type="checkbox" />
              <div class="collapse-title text-sm font-medium">
                Show Generation Details
              </div>
              <div class="collapse-content">
                <pre
                  class="text-xs whitespace-pre-wrap p-2 bg-base-200 rounded-box">{`
Positive: ${positivePrompt}
Seed: ${seed}
Steps: ${steps}
CFG Scale: ${cfg}
                `}</pre>
              </div>
            </div>
          {:else}
            <!-- Placeholder -->
            <div
              class="flex-1 bg-neutral rounded-box flex items-center justify-center"
            >
              <span class="text-neutral-content text-opacity-50">
                Image will appear here
              </span>
            </div>
          {/if}
          <!-- Lightbox Overlay -->
          {#if showLightbox && selectedImage}
            <div
              class="fixed inset-0 z-50 bg-black/80 flex items-center justify-center lightbox-container"
            >
              <div class="relative max-w-4xl max-h-full">
                <!-- Close Button -->
                <button
                  on:click={closeLightbox}
                  class="absolute top-3 right-3 btn btn-ghost btn-circle btn-sm"
                >
                  ✕
                </button>

                <!-- Download Button -->
                <button
                  on:click={() => downloadImage(selectedImage.url)}
                  class="absolute top-3 left-3 btn btn-primary btn-sm"
                >
                  📥
                </button>

                <!-- Image Container -->
                <img
                  src={selectedImage.url}
                  alt="Generated"
                  class="rounded-box max-w-full max-h-full object-contain"
                />
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </form>
</main>

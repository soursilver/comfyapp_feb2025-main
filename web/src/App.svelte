<script>
  import { onMount } from "svelte";

  let imageUrl = "";
  let status = "Ready";
  let clientId = "";
  let serverAddress = "http://localhost:8188";

  // Form bindings
  let positivePrompt = "Hyperrealistic image of...";
  let negativePrompt = "lowres, bad anatomy...";
  let seed = Math.floor(Math.random() * 1000000000);
  let steps = 25;
  let cfg = 3.5;
  let selectedModel = "NewReality_FLUXS1D_Alpha2.safetensors";
  let selectedSize = "1024x1024";

  const modelOptions = [
    "NewReality_FLUXS1D_Alpha2.safetensors",
    "RealisticModel.safetensors",
    "DreamlikeModel.safetensors",
  ];

  const sizeOptions = [
    { label: "1024x1024", width: 1024, height: 1024 },
    { label: "512x512", width: 512, height: 512 },
    { label: "800x600", width: 800, height: 600 },
  ];

  // Load your workflow JSON
  let promptTemplate = {
    "6": {
      inputs: {
        text: "A young woman with long dark hair stands in a snowy forest",
        clip: ["38", 0],
      },
      class_type: "CLIPTextEncode",
      _meta: {
        title: "CLIP Text Encode (Positive Prompt)",
      },
    },
    "8": {
      inputs: {
        samples: ["31", 0],
        vae: ["39", 0],
      },
      class_type: "VAEDecode",
      _meta: {
        title: "VAE Decode",
      },
    },
    "9": {
      inputs: {
        filename_prefix: "ComfyUI",
        images: ["8", 0],
      },
      class_type: "SaveImage",
      _meta: {
        title: "Save Image",
      },
    },
    "30": {
      inputs: {
        ckpt_name: "NewReality_FLUXS1D_Alpha2.safetensors",
      },
      class_type: "CheckpointLoaderSimple",
      _meta: {
        title: "Load Checkpoint",
      },
    },
    "31": {
      inputs: {
        seed: 646960540499716,
        steps: 20,
        cfg: 3.5,
        sampler_name: "euler",
        scheduler: "simple",
        denoise: 1,
        model: ["37", 0],
        positive: ["35", 0],
        negative: ["33", 0],
        latent_image: ["40", 4],
      },
      class_type: "KSampler",
      _meta: {
        title: "KSampler",
      },
    },
    "33": {
      inputs: {
        text: "",
        clip: ["38", 0],
      },
      class_type: "CLIPTextEncode",
      _meta: {
        title: "CLIP Text Encode (Negative Prompt)",
      },
    },
    "35": {
      inputs: {
        guidance: 3.5,
        conditioning: ["6", 0],
      },
      class_type: "FluxGuidance",
      _meta: {
        title: "FluxGuidance",
      },
    },
    "37": {
      inputs: {
        max_shift: 1.15,
        base_shift: 0.5,
        width: ["40", 0],
        height: ["40", 1],
        model: ["30", 0],
      },
      class_type: "ModelSamplingFlux",
      _meta: {
        title: "ModelSamplingFlux",
      },
    },
    "38": {
      inputs: {
        clip_name1: "clip_l.safetensors",
        clip_name2: "t5xxl_fp8_e4m3fn.safetensors",
        type: "flux",
      },
      class_type: "DualCLIPLoader",
      _meta: {
        title: "DualCLIPLoader",
      },
    },
    "39": {
      inputs: {
        vae_name: "FLUX_vae.safetensors",
      },
      class_type: "VAELoader",
      _meta: {
        title: "Load VAE",
      },
    },
    "40": {
      inputs: {
        width: 1024,
        height: 1024,
        aspect_ratio: "custom",
        swap_dimensions: "Off",
        upscale_factor: 1,
        batch_size: 1,
      },
      class_type: "CR SDXL Aspect Ratio",
      _meta: {
        title: "🔳 CR SDXL Aspect Ratio",
      },
    },
  };

  onMount(() => {
    clientId = crypto.randomUUID();
  });

  async function generateImage(e) {
    e.preventDefault();
    status = "Generating...";

    // Enqueue prompt via HTTP
    const apiUrl = new URL(serverAddress);
    const queueUrl = `${apiUrl.origin}/prompt`;
    const prompt = structuredClone(promptTemplate);

    try {
      // Queue prompt
      const response = await fetch(queueUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, client_id: clientId }),
      });
      const { prompt_id } = await response.json();

      // Test WebSocket connection
      if (await testWebSocketConnection(apiUrl)) {
        await waitForWebSocketMessage(prompt_id, apiUrl);
      } else {
        await pollForCompletion(prompt_id, apiUrl);
      }

      // Fetch image
      const historyResponse = await fetch(
        `${apiUrl.origin}/history/${prompt_id}`
      );
      const history = await historyResponse.json();
      const imgData = history[prompt_id]?.outputs?.["9"]?.images?.[0];
      imageUrl = `${apiUrl.origin}/view?filename=${imgData.filename}&subfolder=${encodeURIComponent(imgData.subfolder)}&type=${imgData.type}`;
      status = "Ready";
    } catch (err) {
      status = `Error: ${err.message}`;
    }
  }

  // Test WebSocket connection
  async function testWebSocketConnection(apiUrl) {
    return new Promise((resolve) => {
      const wsProtocol = apiUrl.protocol === "https:" ? "wss" : "ws";
      const wsUrl = `${wsProtocol}://${apiUrl.host}/ws?clientId=${crypto.randomUUID()}`;

      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        socket.close();
        resolve(true);
      };

      socket.onerror = () => {
        resolve(false);
      };

      setTimeout(() => {
        socket.close();
        resolve(false);
      }, 2000);
    });
  }

  // Wait for WebSocket message
  async function waitForWebSocketMessage(promptId, apiUrl) {
    return new Promise((resolve, reject) => {
      const wsProtocol = apiUrl.protocol === "https:" ? "wss" : "ws";
      const wsUrl = `${wsProtocol}://${apiUrl.host}/ws?clientId=${clientId}`;
      const socket = new WebSocket(wsUrl);

      socket.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "executing" && msg.data.prompt_id === promptId) {
          resolve();
        }
      };

      socket.onerror = (err) => reject(err);
      socket.onclose = () => reject(new Error("WebSocket closed"));
    });
  }

  // Poll for completion
  async function pollForCompletion(promptId, apiUrl) {
    return new Promise((resolve, reject) => {
      let attempts = 0;
      const maxAttempts = 30;

      const interval = setInterval(async () => {
        attempts++;
        try {
          const historyResponse = await fetch(
            `${apiUrl.origin}/history/${promptId}`
          );
          const history = await historyResponse.json();
          if (history[promptId]?.outputs?.["9"]?.images?.[0]) {
            clearInterval(interval);
            resolve();
          }
        } catch (err) {
          // ignore errors
        }

        if (attempts >= maxAttempts) {
          clearInterval(interval);
          reject(new Error("Polling timeout"));
        }
      }, 2000);
    });
  }
</script>

<main class="container mx-auto px-4 py-6">
  <form on:submit={generateImage} class="flex flex-col md:flex-row gap-6">
    <!-- Left Panel - Controls -->
    <div class="w-full md:w-1/2 space-y-6">
      <div class="card bg-base-100 shadow-xl p-6">
        <h2 class="text-xl font-bold mb-4">Generation Settings</h2>

        <!-- Server Address Input -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Server Address</span>
          </label>
          <input
            type="text"
            bind:value={serverAddress}
            class="input input-bordered w-full"
            placeholder="http://localhost:8188 or https://your-tunnel.cloudflareaccess.com"
          />
        </div>

        <!-- Model Selection -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Model</span>
          </label>
          <select
            bind:value={selectedModel}
            class="select select-bordered w-full max-w-xs"
          >
            {#each modelOptions as model}
              <option value={model}>{model}</option>
            {/each}
          </select>
        </div>

        <!-- Positive Prompt -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-semibold">Positive Prompt</span>
          </label>
          <textarea
            bind:value={positivePrompt}
            rows="4"
            class="textarea textarea-bordered textarea-lg w-full"
            placeholder="Describe what you want to generate..."
          />
        </div>

        <!-- Negative Prompt -->
        <div class="form-control mt-4">
          <label class="label">
            <span class="label-text font-semibold">Negative Prompt</span>
          </label>
          <textarea
            bind:value={negativePrompt}
            rows="4"
            class="textarea textarea-bordered textarea-lg w-full"
            placeholder="What to exclude from the image..."
          />
        </div>

        <!-- Parameters Grid -->
        <div class="grid grid-cols-1 md:grid-cols-1 gap-4 mt-6">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Seed</span>
            </label>
            <input
              type="number"
              bind:value={seed}
              class="input input-bordered w-full"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Steps ({steps})</span>
            </label>
            <input
              type="range"
              bind:value={steps}
              min="1"
              max="50"
              class="range range-primary"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">CFG Scale ({cfg})</span>
            </label>
            <input
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
            <label class="label">
              <span class="label-text font-semibold">Image Size</span>
            </label>
            <select
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
            disabled={status !== "Ready"}
          >
            {#if status === "Generating..."}
              <span class="loading loading-spinner"></span>
              Generating
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
            <figure class="flex-1 bg-neutral rounded-box overflow-hidden">
              <img
                src={imageUrl}
                alt="Generated image"
                class="w-full h-auto object-contain"
              />
            </figure>

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
Negative: ${negativePrompt}
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
        </div>
      </div>
    </div>
  </form>
</main>

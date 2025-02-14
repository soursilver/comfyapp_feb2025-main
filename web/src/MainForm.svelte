<script>
  import { onMount } from "svelte";

  // props
  export let useUnetModels = false;
  export let serverAddress = "";
  
  // variables
  let clientId;
  let ws;
  let imageUrl = "";
  let status = "Ready";
  let promptId;
  

  // Form bindings
  let positivePrompt =
    "Hyperrealistic image of futuristic futuristic scene, realistic style";
  let negativePrompt = "lowres, bad anatomy...";
  let seed = Math.floor(Math.random() * 1000000000);
  let steps = 15;
  let cfg = 3.5;
  let selectedModel = "NewReality_FLUXS1D_Alpha2.safetensors";
  let loadingModels = true;
  let selectedSize = "1024x1024";
  let modelOptions = [];

  let sizeOptions = [
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

  onMount(async () => {
    console.log("Server address:", serverAddress);
    clientId = crypto.randomUUID();
    if (!serverAddress) return;
    try {
      const response = await fetch(`${serverAddress}/object_info`);
      const data = await response.json();
      const models = data.CheckpointLoaderSimple.input.required.ckpt_name[0];
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

  // Reactive statement to watch serverAddress changes
  $: serverAddress, useUnetModels, fetchModels();

  async function fetchModels() {
    if (!serverAddress) return;
    
    loadingModels = true;
    try {
      const response = await fetch(`${serverAddress}/object_info`);
      const data = await response.json();
      
      const modelPath = useUnetModels 
        ? "UNETLoader.input.required.unet_name[0]"
        : "CheckpointLoaderSimple.input.required.ckpt_name[0]";
      
      modelOptions = getNestedProperty(data, modelPath) || [];
    } catch (error) {
      console.error("Error loading models:", error);
      modelOptions = ["DefaultModel.safetensors"];
    } finally {
      loadingModels = false;
    }
  }

  // Add helper function to access nested properties
  function getNestedProperty(obj, path) {
  return path.split('.').reduce((acc, part) => {
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
    status = "Generating...";

    try {
      // Prepare prompt
      const apiUrl = new URL(serverAddress);
      const prompt = structuredClone(promptTemplate);
      prompt["6"].inputs.text = positivePrompt;
      prompt["33"].inputs.text = negativePrompt;
      prompt["31"].inputs.seed = seed;
      prompt["31"].inputs.steps = steps;
      prompt["31"].inputs.cfg = cfg;
      prompt["30"].inputs.ckpt_name = selectedModel;
      prompt["40"].inputs.width = selectedSize.split("x")[0];
      prompt["40"].inputs.height = selectedSize.split("x")[1];

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
        `${apiUrl.origin}/history/${promptId}`
      );
      const history = await historyResponse.json();
      const imgData = history[promptId]?.outputs?.["9"]?.images?.[0];

      if (imgData && imgData.filename) {
        imageUrl = `${apiUrl.origin}/view?filename=${imgData.filename}&subfolder=${encodeURIComponent(
          imgData.subfolder
        )}&type=${imgData.type}`;
        status = "Ready";
      } else {
        throw new Error("Image data not found");
      }
    } catch (err) {
      status = `Error: ${err.message}`;
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
          `${apiUrl.origin}/history/${promptId}`
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

        <!-- Negative Prompt -->
        <div class="form-control mt-4">
          <label class="label" for="negative-prompt">
            <span class="label-text font-semibold">Negative Prompt</span>
          </label>
          <textarea
            id="negative-prompt"
            bind:value={negativePrompt}
            rows="4"
            class="textarea textarea-bordered textarea-lg w-full"
            placeholder="What to exclude from the image..."
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
                alt="Generated"
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

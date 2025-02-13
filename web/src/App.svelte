<script>
  import { onMount } from "svelte";
  let clientId;
  let ws;
  let imageUrl = "";
  let status = "Ready";

  // Form bindings
  let positivePrompt = "Hyperrealistic image of...";
  let negativePrompt = "lowres, bad anatomy...";
  let seed = Math.floor(Math.random() * 1000000000);
  let steps = 25;
  let cfg = 12.5;

  // Load your workflow JSON
  let promptTemplate = {
  "6": {
    "inputs": {
      "text": "A young woman with long dark hair stands in a snowy forest",
      "clip": [
        "38",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "31",
        0
      ],
      "vae": [
        "39",
        0
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "30": {
    "inputs": {
      "ckpt_name": "NewReality_FLUXS1D_Alpha2.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "31": {
    "inputs": {
      "seed": 646960540499716,
      "steps": 20,
      "cfg": 1,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": [
        "37",
        0
      ],
      "positive": [
        "35",
        0
      ],
      "negative": [
        "33",
        0
      ],
      "latent_image": [
        "40",
        4
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "33": {
    "inputs": {
      "text": "",
      "clip": [
        "38",
        0
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Negative Prompt)"
    }
  },
  "35": {
    "inputs": {
      "guidance": 3.5,
      "conditioning": [
        "6",
        0
      ]
    },
    "class_type": "FluxGuidance",
    "_meta": {
      "title": "FluxGuidance"
    }
  },
  "37": {
    "inputs": {
      "max_shift": 1.15,
      "base_shift": 0.5,
      "width": [
        "40",
        0
      ],
      "height": [
        "40",
        1
      ],
      "model": [
        "30",
        0
      ]
    },
    "class_type": "ModelSamplingFlux",
    "_meta": {
      "title": "ModelSamplingFlux"
    }
  },
  "38": {
    "inputs": {
      "clip_name1": "clip_l.safetensors",
      "clip_name2": "t5xxl_fp8_e4m3fn.safetensors",
      "type": "flux"
    },
    "class_type": "DualCLIPLoader",
    "_meta": {
      "title": "DualCLIPLoader"
    }
  },
  "39": {
    "inputs": {
      "vae_name": "FLUX_vae.safetensors"
    },
    "class_type": "VAELoader",
    "_meta": {
      "title": "Load VAE"
    }
  },
  "40": {
    "inputs": {
      "width": 1024,
      "height": 1024,
      "aspect_ratio": "custom",
      "swap_dimensions": "Off",
      "upscale_factor": 1,
      "batch_size": 1
    },
    "class_type": "CR SDXL Aspect Ratio",
    "_meta": {
      "title": "🔳 CR SDXL Aspect Ratio"
    }
  }
}

  onMount(() => {
    clientId = crypto.randomUUID();
    connectWebSocket();
  });

  function connectWebSocket() {
    ws = new WebSocket(`ws://127.0.0.1:8188/ws?clientId=${clientId}`);

    ws.onmessage = async (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "executing" && msg.data.node === null) {
        status = "Fetching image...";
        const history = await getHistory(msg.data.prompt_id);
        const imgData = history[msg.data.prompt_id].outputs["9"].images[0];
        imageUrl = `http://127.0.0.1:8188/view?filename=${
          imgData.filename
        }&subfolder=${encodeURIComponent(imgData.subfolder)}&type=${imgData.type}`;
        status = "Ready";
      }
    };
  }

  async function queuePrompt(prompt) {
    const response = await fetch("http://127.0.0.1:8188/prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, client_id: clientId }),
    });
    return await response.json();
  }

  async function getHistory(promptId) {
    const response = await fetch(`http://127.0.0.1:8188/history/${promptId}`);
    return await response.json();
  }

  async function generateImage(e) {
    e.preventDefault();
    status = "Generating...";

    const prompt = structuredClone(promptTemplate);
    prompt["6"].inputs.text = positivePrompt;
    prompt["33"].inputs.text = negativePrompt;
    prompt["31"].inputs.seed = seed;

    try {
      const { prompt_id } = await queuePrompt(prompt);
    } catch (err) {
      status = `Error: ${err.message}`;
    }
  }
</script>

<main>
  <form on:submit={generateImage}>
    <div class="grid">
      <div class="controls">
        <label
          >Positive Prompt
          <textarea bind:value={positivePrompt} rows="4" />
        </label>

        <label
          >Negative Prompt
          <textarea bind:value={negativePrompt} rows="4" />
        </label>

        <div class="grid">
          <label
            >Seed
            <input type="number" bind:value={seed} />
          </label>
          <label
            >Steps
            <input type="range" bind:value={steps} min="1" max="50" />
            {steps}
          </label>
          <label
            >CFG Scale
            <input type="range" bind:value={cfg} min="1" max="20" step="0.5" />
            {cfg}
          </label>
        </div>

        <button type="submit" disabled={status !== "Ready"}>
          {status}
        </button>
      </div>

      <div class="output">
        {#if imageUrl}
          <img src={imageUrl} alt="Generated image" />
          <div class="metadata">
            <h3>Metadata</h3>
            <pre>Positive: {positivePrompt}
                  Negative: {negativePrompt}
                  Seed: {seed}</pre>
          </div>
        {/if}
      </div>
    </div>
  </form>
</main>

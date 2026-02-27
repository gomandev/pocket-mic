# Railway Deployment Guide for PocketMic Python Backend

Since the Python backend requires heavy audio processing and background tasks, deploying it to a platform like Railway is highly recommended over Vercel (which is built for fast, serverless frontend operations).

Follow these steps to deploy the `services/audio-production` backend:

## 1. Create a Railway Account
Go to [Railway.app](https://railway.app/) and sign up using your GitHub account.

## 2. Deploy the Repository
1. In your Railway dashboard, click **"New Project"**.
2. Select **"Deploy from GitHub repo"**.
3. Select your repository: `gomandev/pocket-mic`.
4. **CRITICAL STEP**: Before it builds (or if the first build fails), go to the deployment's **Settings** tab.
5. Scroll down to **Service > Root Directory** and enter: `/services/audio-production`.
   *(This tells Railway to ignore the `package.json` and Next.js frontend, and only build your Python background worker!)*

## 3. Set Environment Variables
Once the project is created, it will likely fail its first build because it's missing the secret keys. 
1. Click on your new deployment tile down below.
2. Go to the **Variables** tab.
3. Add the following variables (copy values from your local `.env` file):
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
   - `REPLICATE_API_TOKEN`

## 4. Generate a Public Domain
1. In the Railway dashboard for your service, go to the **Settings** tab.
2. Scroll to the **Environment** section.
3. Under **Domains**, click **"Generate Domain"**.
4. Railway will provide a URL like `pocket-mic-production.up.railway.app`.

## 5. Update the Next.js Frontend
Now that your Python backend is live on Railway, you need to tell your Vercel frontend where to find it.

1. Open your `app/api/jobs/[id]/master/route.ts` file.
2. Change the hardcoded proxy from `http://localhost:8000/master` to your new Railway URL:
   ```typescript
   // Old
   const pythonRes = await fetch("http://localhost:8000/master", { ... })
   
   // New
   const pythonUrl = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";
   const pythonRes = await fetch(`${pythonUrl}/master`, { ... })
   ```
3. Update your frontend environment variables in Vercel to include:
   `PYTHON_BACKEND_URL=https://<your-railway-domain>.railway.app`

## 6. Testing
Trigger a new mix or master in the PocketMic UI. You should see logs appear live in the Railway dashboard's **Deployments** tab under **View Logs**.

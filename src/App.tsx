import { useState } from "react";
import "./index.css";
import Chart from "./components/Chart";
import Grid from "./components/Grid";
import Button from "./components/Button";
import { demoData } from "./data/demoData";
import type { Row } from "./types/Row";
import { processData, type ProcessResponse } from "./api/process";

function App() {
 
  const [data, setData] = useState<Row[]>(demoData)
  const [sigmaV0, setSigmaV0] = useState<string>("75")
  const [result, setResult] = useState<ProcessResponse | null>(null)
  const [warningMessage, setWarningMessage] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  async function handleProcess() {
    const sigmaV0Value = Number(sigmaV0)
    if (!Number.isFinite(sigmaV0Value) || sigmaV0Value <= 0) {
      setWarningMessage("Initial effective stress must be a positive number.")
      return
    }

    setIsProcessing(true)
    setWarningMessage(null)
    try {
      const next = await processData({ sigmaV0: sigmaV0Value, rows: data })
      setResult(next)
    } catch (e) {
      const message = e instanceof Error ? e.message : "Processing failed."
      setWarningMessage(message)
    } finally {
      setIsProcessing(false)
    }
  }

    return (
      <main className='min-h-screen flex flex-col bg-linear-to-r from-slate-800 to-slate-950 text-white text-sm sm:text-base'>
        <div>
          <label>
            Initial Effective Stress, P'v0: {" "}
            <input
              type="number"
              value={sigmaV0}
              onChange={(e) => setSigmaV0(e.target.value)}
              min={0}
            />
          </label>
          {warningMessage != null && <div>{warningMessage}</div>}
        </div>
        <Chart
          data={data}
          compressionIdx={result?.compressionIdx ?? null}
          recompressionIdx={result?.recompressionIdx ?? null}
          warnings={result?.warnings ?? []}
        />
        <Grid data={data} onChange={setData} />
        <Button onClick={handleProcess} text={isProcessing ? "Processing..." : "Process"} />
      </main>
    )
}

export default App

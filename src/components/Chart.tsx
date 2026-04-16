import { useMemo } from "react";
import type { Row } from "../types/Row";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LinearScale,
  LogarithmicScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  type ChartData,
  type ChartOptions,
  type TooltipItem,
} from "chart.js";

ChartJS.register(LinearScale, LogarithmicScale, PointElement, LineElement, Title, Tooltip)

type Props = {
  data: Row[]
  compressionIdx: number | null
  recompressionIdx: number | null
  warnings: string[]
}

function Chart({ data, compressionIdx, recompressionIdx, warnings }: Props) {

  const points = useMemo(() => data.filter((d): d is Required<Row> =>
            d.pressure != null &&
            d.void_ratio != null &&
            d.pressure > 0
        ).map((d) => ({
          x: d.pressure,
          y: d.void_ratio,
        })),
    [data]
  )

  const chartData: ChartData<"line"> = useMemo(
    () => ({
      datasets: [
        {
          label: "Void Ratio vs Pressure",
          data: points,
          borderColor: "rgba(75, 192, 192, 0.6)",
          backgroundColor: "rgba(75, 192, 192, 1)",
          tension: 0.2,
          pointRadius: 3,
        },
      ],
    }),
    [points]
  )

  const chartOptions: ChartOptions<"line"> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      // legend: { position: "bottom" },
      title: {
        display: true,
        text: "e-log P Curve",
      },
      tooltip: {
        callbacks: {
          label: (ctx: TooltipItem<"line">) => {
            const x = ctx.parsed.x ?? 0;
            const y = ctx.parsed.y ?? 0;
            return `Pressure: ${x.toFixed(2)}, Void Ratio: ${y.toFixed(3)}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "logarithmic",
        suggestedMin: 0.001,
        title: {
          display: true,
          text: "Pressure",
        },
      },
      y: {
        title: {
          display: true,
          text: "Void Ratio",
        },
      },
    },
  }

  return (
    <div style={{ height: "400px", width: "100%" }}>
      <div>
        <div>
          {compressionIdx != null && <span>CompressionIdx: {compressionIdx.toFixed(3)}</span>}
          {recompressionIdx != null && <span> RecompressionIdx: {recompressionIdx.toFixed(3)}</span>}
        </div>
        {warnings.length > 0 && (
          <div>
            {warnings.map((w, i) => (
              <div key={i}>{w}</div>
            ))}
          </div>
        )}
      </div>
      <Line data={chartData} options={chartOptions} />
    </div>
  )
}

export default Chart

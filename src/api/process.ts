import axios from "axios"
import type { Row } from "../types/Row";

export type ProcessRequest = {
  sigmaV0: number;
  rows: Row[];
};

export type ProcessResponse = {
  compressionIdx: number | null;
  recompressionIdx: number | null;
  warnings: string[];
};

const api = axios.create({baseURL: "http://localhost:8000"})

export async function processData(request: ProcessRequest): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>("/process", request)
  return data
}


import axios from "axios";
import type { Row } from "../types/Row";

export type ProcessRequest = {
  sigmaV0: number;
  rows: Row[];
};

export type Point = { x: number; y: number };

export type ProcessResponse = {
  segment1: Point[];
  segment2: Point[];
  intersection: Point;
  compressionIdx: number | null;
  recompressionIdx: number | null;
  warnings: string[];
};

const api = axios.create({
  baseURL: ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "").trim(),
});

export async function processData(request: ProcessRequest): Promise<ProcessResponse> {
  const { data } = await api.post<ProcessResponse>("/process", request);
  return data;
}


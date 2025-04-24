"use strict";

import { z } from "zod";

const envSchema = z.object({
  TIMEZONE: z.string().default("GMT+7"),
  API_BASE_URL: z.string().url(),
  MONGO_HOST: z.string(),
  MONGO_PORT: z.string(),
  MONGO_DATABASE: z.string(),
  MONGO_USER: z.string().optional(),
  MONGO_PASSWORD: z.string().optional(),
  MONGO_AUTH_SOURCE: z.string().optional(),
  MONGO_AUTH_MECHANISM: z.string().optional(),
  PAGE_SIZE: z.string().transform(Number).default("50"),
  TRADES_TO_FETCH: z.string().transform(Number).default("10000"),
  DAYS_TO_FETCH: z.string().transform(Number).default("1"),
  TRANSPORT_TYPE: z.enum(["stdio", "sse"]).default("stdio"),
  PORT: z.string().default("8080")
});

export const getConfig = () => {
  const result = envSchema.safeParse(process.env);
  
  if (!result.success) {
    throw new Error(`Configuration error: ${result.error.message}`);
  }
  
  return result.data;
}; 
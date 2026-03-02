export type DashboardView = "map" | "sales" | "feedback" | "chat";

export interface FilterOptions {
  products: string[];
  countries: string[];
  regions: string[];
  minDate: string;
  maxDate: string;
}

export interface DashboardFilters {
  product: string;
  country: string;
  region: string;
  dateFrom: string;
  dateTo: string;
}

export interface MetricCard {
  label: string;
  value: number;
  delta: number;
  format: "currency" | "number" | "percent";
  caption: string;
}

export interface MapPoint {
  lat: number;
  lng: number;
  label: string;
}

export interface MapConnection {
  start: MapPoint;
  end: MapPoint;
  revenue: number;
  orders: number;
  share: number;
  sentiment?: number;
}

export interface RevenuePoint {
  date: string;
  revenue: number;
  orders: number;
}

export interface RegionPerformance {
  region: string;
  revenue: number;
  orders: number;
  avgOrderValue: number;
  share: number;
}

export interface CountryPerformance {
  country: string;
  region: string;
  revenue: number;
  orders: number;
  growth: number;
  lat: number;
  lng: number;
}

export interface ProductMixRow {
  product: string;
  revenue: number;
  units: number;
  share: number;
}

export interface SalesDashboardData {
  generatedAt: string;
  filters: FilterOptions;
  appliedFilters: DashboardFilters;
  heroMetrics: MetricCard[];
  mapConnections: MapConnection[];
  revenueTrend: RevenuePoint[];
  regionPerformance: RegionPerformance[];
  countryPerformance: CountryPerformance[];
  productMix: ProductMixRow[];
  spotlights: string[];
}

export interface SentimentTrendPoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

export interface CampaignImpactRow {
  campaignId: string;
  product: string;
  feedbackCount: number;
  avgSentiment: number;
  linkedRevenue: number;
  headline: string;
}

export interface TopicSignal {
  topic: string;
  count: number;
  tone: "positive" | "neutral" | "negative";
}

export interface FeedbackExcerpt {
  id: number;
  username: string;
  feedbackDate: string;
  campaignId: string;
  product: string;
  country: string;
  sentimentLabel: "positive" | "neutral" | "negative";
  sentimentScore: number;
  comment: string;
}

export interface CountrySentimentRow {
  country: string;
  region: string;
  feedbackCount: number;
  avgSentiment: number;
  positiveShare: number;
  negativeShare: number;
  lat: number;
  lng: number;
}

export interface FeedbackDashboardData {
  generatedAt: string;
  filters: FilterOptions;
  appliedFilters: DashboardFilters;
  heroMetrics: MetricCard[];
  sentimentTrend: SentimentTrendPoint[];
  campaignImpact: CampaignImpactRow[];
  topicSignals: TopicSignal[];
  recentFeedback: FeedbackExcerpt[];
  sentimentByCountry: CountrySentimentRow[];
  mapConnections: MapConnection[];
  briefs: string[];
}

export interface RagCitation {
  feedbackId: number;
  campaignId: string;
  product: string;
  country: string;
  feedbackDate: string;
  sentimentLabel: string;
  score: number;
  comment: string;
}

export interface RagResponse {
  answer: string;
  retrievalMode: string;
  citations: RagCitation[];
}

export interface SalesRow {
  id: number;
  username: string;
  saleDate: string;
  country: string;
  region: string;
  product: string;
  quantity: number;
  unitPrice: number;
  totalAmount: number;
}

export interface FeedbackRow {
  id: number;
  username: string;
  feedbackDate: string;
  campaignId: string;
  product: string;
  country: string;
  region: string;
  sentimentLabel: string;
  sentimentScore: number;
  comment: string;
}

export interface CampaignRow {
  campaignId: string;
  product: string;
}

export interface DataPreview {
  sales: SalesRow[];
  feedback: FeedbackRow[];
  campaigns: CampaignRow[];
}

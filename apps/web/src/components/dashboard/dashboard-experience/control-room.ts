import type {
  FeedbackDashboardData,
  SalesDashboardData,
} from "@/lib/types";
import type { ChatMessage, ChainNode, ControlRoomNarrative, PrioritySignal } from "./types";
import { compactCurrencyFormatter } from "./types";
import { sentimentScoreLabel, truncateMiddle } from "./utils";

export function buildControlRoomState(
  salesData: SalesDashboardData | null,
  feedbackData: FeedbackDashboardData | null,
  latestRetrievalMessage?: ChatMessage,
  lastUserMessage?: ChatMessage,
) {
  const leadMarket = salesData?.countryPerformance[0] ?? null;
  const fastestGrowthMarket =
    [...(salesData?.countryPerformance ?? [])].sort((left, right) => right.growth - left.growth)[0] ??
    null;
  const topProduct = salesData?.productMix[0] ?? null;
  const revenueLinkedCampaign =
    [...(feedbackData?.campaignImpact ?? [])].sort(
      (left, right) => right.linkedRevenue - left.linkedRevenue,
    )[0] ?? null;
  const healthiestCampaign =
    [...(feedbackData?.campaignImpact ?? [])].sort(
      (left, right) => right.avgSentiment - left.avgSentiment,
    )[0] ?? null;
  const positiveTopic =
    [...(feedbackData?.topicSignals ?? [])]
      .filter((topic) => topic.tone === "positive")
      .sort((left, right) => right.count - left.count)[0] ?? null;
  const negativeTopic =
    [...(feedbackData?.topicSignals ?? [])]
      .filter((topic) => topic.tone === "negative")
      .sort((left, right) => right.count - left.count)[0] ?? null;
  const fragileCountry =
    [...(feedbackData?.sentimentByCountry ?? [])].sort(
      (left, right) => left.avgSentiment - right.avgSentiment,
    )[0] ?? null;
  const exposedRevenue =
    fragileCountry
      ? salesData?.countryPerformance.find((row) => row.country === fragileCountry.country) ?? null
      : null;
  const reinforcingCountry =
    leadMarket
      ? feedbackData?.sentimentByCountry.find((row) => row.country === leadMarket.country) ?? null
      : null;

  const narrative: ControlRoomNarrative = {
    summary:
      leadMarket && revenueLinkedCampaign
        ? `Revenue is being led by ${leadMarket.country} and reinforced by ${revenueLinkedCampaign.campaignId} on ${revenueLinkedCampaign.product}. ${positiveTopic ? `${positiveTopic.topic} is the strongest positive topic signal in the current window.` : "Positive feedback remains supportive in the strongest markets."}`
        : "Sales, feedback, and retrieval signals will align here once enough data is available.",
    risk:
      fragileCountry && negativeTopic
        ? `${negativeTopic.topic} friction is rising in ${fragileCountry.country}, where sentiment is ${sentimentScoreLabel(fragileCountry.avgSentiment)}.${exposedRevenue ? ` ${compactCurrencyFormatter.format(exposedRevenue.revenue)} in revenue is exposed in that market.` : ""}`
        : fragileCountry
          ? `${fragileCountry.country} is the weakest sentiment market in the selected window.`
          : "No material risk signal is visible yet in the selected slice.",
    opportunity:
      revenueLinkedCampaign && healthiestCampaign
        ? `${revenueLinkedCampaign.campaignId} is linking ${compactCurrencyFormatter.format(revenueLinkedCampaign.linkedRevenue)} in sales, while ${healthiestCampaign.campaignId} shows ${sentimentScoreLabel(healthiestCampaign.avgSentiment)} sentiment support.`
        : leadMarket
          ? `${leadMarket.country} is the clearest revenue lever in the selected window.`
          : "No opportunity signal is visible yet.",
    action:
      fragileCountry
        ? `Review campaign execution and checkout experience in ${fragileCountry.country} before the next promotion wave.`
        : fastestGrowthMarket
          ? `Double down on ${fastestGrowthMarket.country} while current momentum is accelerating.`
          : "Keep monitoring the selected slice for a stronger market signal.",
  };

  const prioritySignals: PrioritySignal[] = [
    {
      tone: "positive",
      label: "Key opportunity",
      value: revenueLinkedCampaign?.campaignId ?? leadMarket?.country ?? "Awaiting signal",
      detail:
        revenueLinkedCampaign && leadMarket
          ? `${revenueLinkedCampaign.product} is pairing strong campaign traction with ${compactCurrencyFormatter.format(leadMarket.revenue)} revenue in ${leadMarket.country}.`
          : "No campaign-to-revenue opportunity is strong enough yet.",
    },
    {
      tone: "negative",
      label: "Key risk",
      value: fragileCountry?.country ?? "No risk market",
      detail:
        fragileCountry
          ? `${negativeTopic?.topic ?? "Sentiment"} pressure is building while ${exposedRevenue ? compactCurrencyFormatter.format(exposedRevenue.revenue) : "active"} revenue remains exposed.`
          : "No significant risk concentration is visible yet.",
    },
    {
      tone: "neutral",
      label: "Recommended action",
      value: topProduct?.product ?? "Monitor",
      detail:
        topProduct && fastestGrowthMarket
          ? `Push ${topProduct.product} in ${fastestGrowthMarket.country} and protect execution in the weaker sentiment markets.`
          : narrative.action,
    },
  ];

  const growthChain: ChainNode[] = [
    {
      label: "Campaign",
      value: revenueLinkedCampaign?.campaignId ?? "Awaiting",
      tone: "neutral",
    },
    {
      label: "Sentiment",
      value: reinforcingCountry
        ? sentimentScoreLabel(reinforcingCountry.avgSentiment)
        : healthiestCampaign
          ? sentimentScoreLabel(healthiestCampaign.avgSentiment)
          : "Awaiting",
      tone:
        (reinforcingCountry?.avgSentiment ?? healthiestCampaign?.avgSentiment ?? 0) >= 0.2
          ? "positive"
          : "neutral",
    },
    {
      label: "Topic",
      value: positiveTopic?.topic ?? negativeTopic?.topic ?? "Awaiting",
      tone: positiveTopic ? "positive" : negativeTopic ? "negative" : "neutral",
    },
    {
      label: "Market",
      value: leadMarket?.country ?? fastestGrowthMarket?.country ?? "Awaiting",
      tone: "neutral",
    },
    {
      label: "Revenue",
      value: leadMarket ? compactCurrencyFormatter.format(leadMarket.revenue) : "Awaiting",
      tone: "positive",
    },
  ];

  return {
    narrative,
    prioritySignals,
    growthChain,
    chatMeta: {
      retrievalMode: latestRetrievalMessage?.retrievalMode ?? "waiting",
      generationMode: latestRetrievalMessage?.generationMode ?? "waiting",
      lastPrompt: lastUserMessage ? truncateMiddle(lastUserMessage.content, 34) : "No prompt yet",
      citations: latestRetrievalMessage?.citations?.length ?? 0,
    },
  };
}

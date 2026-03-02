"use client";

import { Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { DataPreview } from "@/lib/types";
import { currencyFormatter } from "./types";

export function DataPreviewSheet({ preview }: { preview: DataPreview | null }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" className="rounded-full border-white/80 bg-white/85">
          <Database className="size-4 sm:mr-2" />
          <span className="hidden sm:inline">Data room</span>
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full border-l-white/80 bg-[rgba(255,250,242,0.95)] sm:max-w-[760px]">
        <SheetHeader className="px-6 pt-6">
          <SheetTitle>Database preview</SheetTitle>
          <SheetDescription>
            Rows currently served by the backend. This is the inspection surface
            for manual checking.
          </SheetDescription>
        </SheetHeader>

        <div className="px-6 pb-6">
          <Tabs defaultValue="sales">
            <TabsList className="w-full justify-start rounded-full bg-white/80">
              <TabsTrigger value="sales">Sales</TabsTrigger>
              <TabsTrigger value="feedback">Feedback</TabsTrigger>
              <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
            </TabsList>

            <TabsContent value="sales" className="mt-4">
              <PreviewTable
                headers={["ID", "User", "Date", "Country", "Product", "Amount"]}
                rows={
                  preview?.sales.map((row) => [
                    String(row.id),
                    row.username,
                    row.saleDate,
                    row.country,
                    row.product,
                    currencyFormatter.format(row.totalAmount),
                  ]) ?? []
                }
              />
            </TabsContent>

            <TabsContent value="feedback" className="mt-4">
              <PreviewTable
                headers={[
                  "ID",
                  "User",
                  "Date",
                  "Campaign",
                  "Product",
                  "Sentiment",
                  "Comment",
                ]}
                rows={
                  preview?.feedback.map((row) => [
                    String(row.id),
                    row.username,
                    row.feedbackDate,
                    row.campaignId,
                    row.product,
                    row.sentimentLabel,
                    row.comment,
                  ]) ?? []
                }
              />
            </TabsContent>

            <TabsContent value="campaigns" className="mt-4">
              <PreviewTable
                headers={["Campaign ID", "Product"]}
                rows={
                  preview?.campaigns.map((row) => [row.campaignId, row.product]) ?? []
                }
              />
            </TabsContent>
          </Tabs>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function PreviewTable({
  headers,
  rows,
}: {
  headers: string[];
  rows: string[][];
}) {
  return (
    <div className="panel h-[640px] p-4">
      <ScrollArea className="h-full">
        <Table>
          <TableHeader>
            <TableRow>
              {headers.map((header) => (
                <TableHead key={header}>{header}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={`${index}-${row[0]}`}>
                {row.map((cell, cellIndex) => (
                  <TableCell key={`${index}-${cellIndex}`} className="max-w-[280px] truncate">
                    {cell}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>
    </div>
  );
}

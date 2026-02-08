'use client'

import { useState, useMemo } from 'react'
import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core"
import styles from './Dashboard.module.css'
import jsPDF from 'jspdf'

interface Report {
  status: string
  alert_level?: string
  alert_message?: string
  summary?: any
  catalog_issues?: any[]
  support_summary?: any
  pricing_actions?: any[]
  warnings?: string[]
  recommendations?: string[]
  metrics?: {
    pricing_pass_rate?: number
    automated_block_rate?: number
    hallucination_rate?: number
    sentiment_score?: number
  }
  validation_flags?: any[]
  audit_log?: any[]
  merchant_locks?: any
  schema_validation_passed?: boolean
  retry_count?: number
  throttle_mode_active?: boolean
  normalized_catalog?: any[]
}

export default function Dashboard() {
  const [report, setReport] = useState<Report | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<{
    products?: File
    messages?: File
    pricing?: File
  }>({})

  // Calculate classification breakdown from raw classifications list
  const classificationBreakdown = useMemo(() => {
    if (!report?.support_summary?.classifications) return null
    
    const counts: Record<string, number> = {}
    report.support_summary.classifications.forEach((item: any) => {
      const type = item.type || 'Unknown'
      counts[type] = (counts[type] || 0) + 1
    })
    return counts
  }, [report?.support_summary])
  // Make report data readable by CopilotKit
  useCopilotReadable({
    description: "The current operations report for the merchant",
    value: report || "No report generated yet"
  })

  // Define CopilotKit action for running operations check
  useCopilotAction({
    name: "runOperationsCheck",
    description: "Run the daily operations check for the merchant, analyzing catalog, support messages, and pricing",
    parameters: [
      {
        name: "merchantId",
        type: "string",
        description: "The merchant ID to run operations for",
        required: false
      }
    ],
    handler: async ({ merchantId }) => {
      return await runOperationsCheck(merchantId || "merchant_001")
    }
  })

  const handleFileUpload = (fileType: 'products' | 'messages' | 'pricing', file: File) => {
    setUploadedFiles(prev => ({
      ...prev,
      [fileType]: file
    }))
  }

  const runOperationsCheck = async (merchantId: string = "merchant_001") => {
    setLoading(true)
    setError(null)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // Prepare input with optional file data
      const input: any = {
        merchant_id: merchantId,
      }

      // If files are uploaded, read and parse them
      if (uploadedFiles.products || uploadedFiles.messages || uploadedFiles.pricing) {
        const fileData: any = {}
        
        if (uploadedFiles.products) {
          const text = await uploadedFiles.products.text()
          fileData.products_csv = text
        }
        
        if (uploadedFiles.messages) {
          const text = await uploadedFiles.messages.text()
          fileData.messages_csv = text
        }
        
        if (uploadedFiles.pricing) {
          const text = await uploadedFiles.pricing.text()
          fileData.pricing_csv = text
        }
        
        input.uploaded_data = fileData
      }
      
      // --- UPDATED FOR LANGGRAPH SERVER API ---
      // We use the /runs/stream endpoint which is standard for LangGraph
      const response = await fetch(`${apiUrl}/runs/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          assistant_id: "salla_ops", // Must match key in langgraph.json
          input,
          stream_mode: "values" // We want the full state updates
        })
      })

      if (!response.ok) {
        throw new Error(`LangGraph API error: ${response.statusText}`)
      }

      // Handle the stream (Server-Sent Events format)
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let finalState = null
      let buffer = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            console.log('Stream reading complete')
            break
          }
          
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          
          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || ''
          
          let currentEvent = ''
          let currentData = ''
          
          for (const line of lines) {
            console.log('Processing line:', JSON.stringify(line))
            
            if (line.startsWith('event:')) {
              currentEvent = line.substring(6).trim()
              console.log('Found event:', currentEvent)
            } else if (line.startsWith('data:')) {
              currentData = line.substring(5).trim()
              console.log('Found data (first 100 chars):', currentData.substring(0, 100))
            } else if (line.trim() === '' && currentEvent && currentData) {
              // Empty line marks end of an SSE message
              console.log('Complete SSE message - Event:', currentEvent)
              
              try {
                if (currentEvent === 'values') {
                  const data = JSON.parse(currentData)
                  console.log('Parsed values event - keys:', Object.keys(data))
                  
                  // Always capture the latest state
                  finalState = data
                  
                  // Log when we see a final_report
                  if (data.final_report) {
                    console.log('Found final_report with status:', data.final_report.status)
                  }
                } else if (currentEvent === 'end') {
                  console.log('Received end event')
                } else if (currentEvent === 'metadata') {
                  console.log('Received metadata event')
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e, "Data:", currentData.substring(0, 200))
              }
              
              // Reset for next message
              currentEvent = ''
              currentData = ''
            }
          }
        }
      }

      console.log('Stream complete')
      console.log('Final state exists:', !!finalState)
      
      if (finalState) {
        console.log('Final state keys:', Object.keys(finalState))
        console.log('Has final_report:', !!finalState.final_report)
        
        if (finalState.final_report) {
          console.log('Final report status:', finalState.final_report.status)
        }
      }

      // Check if we have a final state with a report
      if (!finalState) {
        console.error('No final state captured from stream')
        throw new Error("Workflow completed but no state was captured from the stream.")
      }
      
      if (!finalState.final_report) {
        console.error('Final state has no final_report property')
        console.error('Available keys:', Object.keys(finalState))
        throw new Error("Workflow completed but no report was generated.")
      }
      
      if (!finalState.final_report.status) {
        console.error('Final report has no status')
        console.error('Final report:', finalState.final_report)
        throw new Error("Workflow completed but report has no status.")
      }
      
      const reportData = finalState.final_report
      console.log('Setting report with status:', reportData.status)
      setReport(reportData)
      // ----------------------------------------

      // Generate summary for AI
      const summary = reportData.summary || {}
      const alerts = reportData.alert_level
      const warnings = reportData.warnings?.length || 0
      const catalogIssues = reportData.catalog_issues?.length || 0
      const status = reportData.status
      
      // Handle different workflow outcomes
      if (status === 'FROZEN') {
        return `
          ⚠️ SYSTEM THROTTLED - Operations Frozen
          Status: ${status}
          Alert Level: ${alerts}
          
          The system detected a viral complaint spike and automatically froze all pricing operations.
          This is a safety feature to prevent automated changes during customer service crises.
          
          Recommendations:
          ${reportData.recommendations?.map((r: string) => `- ${r}`).join('\n          ') || '- Review customer complaints immediately'}
          
          The dashboard shows the full alert details.
        `
      }
      
      return `
        Report generated successfully.
        Status: ${status}
        Alert Level: ${alerts}
        Summary:
        - Approved Pricing Changes: ${summary.approved_changes || 0}
        - Blocked Changes: ${summary.blocked_changes || 0}
        - Catalog Issues Found: ${catalogIssues}
        - Warnings: ${warnings}
        
        The dashboard has been updated with the visual details.
      `
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to run operations check'
      setError(errorMsg)
      throw new Error(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const getAlertColor = (level?: string) => {
    switch (level) {
      case 'RED': return '#ef4444'
      case 'YELLOW': return '#f59e0b'
      case 'GREEN': return '#10b981'
      default: return '#6b7280'
    }
  }

  const exportToPDF = () => {
    if (!report) return

    const doc = new jsPDF()
    let yPos = 20
    const pageWidth = doc.internal.pageSize.getWidth()
    const margin = 15

    // Helper function to sanitize text (remove emojis and special characters)
    const sanitizeText = (text: string): string => {
      if (!text) return ''
      // Remove emojis and other problematic Unicode characters
      return text
        .replace(/[\u{1F600}-\u{1F64F}]/gu, '') // Emoticons
        .replace(/[\u{1F300}-\u{1F5FF}]/gu, '') // Misc Symbols and Pictographs
        .replace(/[\u{1F680}-\u{1F6FF}]/gu, '') // Transport and Map
        .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '') // Flags
        .replace(/[\u{2600}-\u{26FF}]/gu, '')   // Misc symbols
        .replace(/[\u{2700}-\u{27BF}]/gu, '')   // Dingbats
        .replace(/[\u{FE00}-\u{FE0F}]/gu, '')   // Variation Selectors
        .replace(/[\u{1F900}-\u{1F9FF}]/gu, '') // Supplemental Symbols and Pictographs
        .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '') // Chess Symbols
        .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '') // Symbols and Pictographs Extended-A
        .replace(/[^\x00-\x7F]/g, (char) => {    // Replace other non-ASCII with safe alternatives
          const replacements: { [key: string]: string } = {
            '\u2013': '-',  // en dash
            '\u2014': '-',  // em dash
            '\u2018': "'",  // left single quote
            '\u2019': "'",  // right single quote
            '\u201C': '"',  // left double quote
            '\u201D': '"',  // right double quote
            '\u2026': '...', // ellipsis
            '\u2022': '*',  // bullet
            '\u2192': '>',  // right arrow
            '\u2190': '<',  // left arrow
            '\u2191': '^',  // up arrow
            '\u2193': 'v',  // down arrow
            '\u2713': 'v',  // check mark
            '\u2717': 'x',  // ballot x
            '\u26A0': '!',  // warning sign
            '\u26A1': '!',  // high voltage
            '\u2605': '*',  // black star
            '\u2606': '*'   // white star
          }
          return replacements[char] || ''
        })
        .trim()
    }

    // Helper function to draw colored box
    const drawBox = (x: number, y: number, width: number, height: number, bgColor: string, borderColor?: string) => {
      doc.setFillColor(bgColor)
      doc.rect(x, y, width, height, 'F')
      if (borderColor) {
        doc.setDrawColor(borderColor)
        doc.setLineWidth(0.5)
        doc.rect(x, y, width, height, 'S')
      }
    }

    // Helper function to convert hex color to RGB
    const hexToRgb = (hex: string) => {
      const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
      return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
      } : { r: 0, g: 0, b: 0 }
    }

    // Helper function for section headers (no emojis)
    const drawSectionHeader = (title: string, y: number, icon?: string) => {
      // Draw a colored bar for the section
      const rgb = hexToRgb('#667eea')
      drawBox(margin, y - 3, 3, 10, '#667eea')
      
      doc.setFontSize(13)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(55, 65, 81)
      doc.text(sanitizeText(title), margin + 6, y + 4)
      return y + 12
    }

    // Title with gradient effect (simulated with colored box)
    const headerRgb = hexToRgb('#667eea')
    drawBox(0, 10, pageWidth, 20, '#667eea')
    doc.setFontSize(20)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(255, 255, 255)
    doc.text('SALLA OPERATIONS REPORT', pageWidth / 2, 22, { align: 'center' })
    yPos = 38

    // Alert Level Badge
    const alertColor = report.alert_level === 'RED' ? '#ef4444' : 
                       report.alert_level === 'YELLOW' ? '#f59e0b' : 
                       report.alert_level === 'GREEN' ? '#10b981' : '#6b7280'
    drawBox(pageWidth - margin - 35, yPos, 30, 8, alertColor)
    doc.setFontSize(10)
    doc.setFont('helvetica', 'bold')
    doc.setTextColor(255, 255, 255)
    doc.text(report.alert_level || 'N/A', pageWidth - margin - 30, yPos + 5.5)
    
    doc.setTextColor(0, 0, 0)
    doc.setFontSize(11)
    doc.setFont('helvetica', 'normal')
    doc.text(`Status: ${report.status || 'N/A'}`, margin, yPos + 5)
    yPos += 15

    // Alert Message (for FROZEN status)
    if (report.alert_message) {
      drawBox(margin, yPos, pageWidth - 2 * margin, 25, '#fee2e2', '#ef4444')
      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(127, 29, 29)
      const splitMessage = doc.splitTextToSize(sanitizeText(report.alert_message), pageWidth - 2 * margin - 10)
      doc.text(splitMessage, margin + 5, yPos + 5)
      yPos += 30
    }

    // Summary Section with boxes
    if (report.summary) {
      yPos = drawSectionHeader('SUMMARY', yPos)
      
      const boxWidth = (pageWidth - 2 * margin - 9) / 4
      const summaryData = [
        { label: 'Total Products', value: report.summary.total_products || 0 },
        { label: 'Approved', value: report.summary.approved_changes || 0 },
        { label: 'Blocked', value: report.summary.blocked_changes || 0 },
        { label: 'Locked', value: report.summary.locked_products || 0 }
      ]

      summaryData.forEach((item, idx) => {
        const xPos = margin + idx * (boxWidth + 3)
        drawBox(xPos, yPos, boxWidth, 18, '#f9fafb', '#e5e7eb')
        doc.setFontSize(8)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(107, 114, 128)
        doc.text(item.label, xPos + boxWidth / 2, yPos + 6, { align: 'center' })
        doc.setFontSize(16)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(31, 41, 55)
        doc.text(String(item.value), xPos + boxWidth / 2, yPos + 14, { align: 'center' })
      })
      yPos += 25
    }

    // Reliability Metrics Section
    if (report.metrics) {
      if (yPos > 240) {
        doc.addPage()
        yPos = 20
      }
      
      yPos = drawSectionHeader('RELIABILITY METRICS', yPos)
      
      const metricsData = [
        { 
          label: 'Pass Rate', 
          value: `${report.metrics.pricing_pass_rate?.toFixed(1) || '0.0'}%`,
          target: '>= 80%',
          status: (report.metrics.pricing_pass_rate || 0) >= 80 ? 'good' : 'warning'
        },
        { 
          label: 'Block Rate', 
          value: `${report.metrics.automated_block_rate?.toFixed(1) || '0.0'}%`,
          target: '<= 10%',
          status: (report.metrics.automated_block_rate || 0) <= 10 ? 'good' : 'warning'
        },
        { 
          label: 'Hallucinations', 
          value: `${report.metrics.hallucination_rate?.toFixed(1) || '0.0'}%`,
          target: '0%',
          status: (report.metrics.hallucination_rate || 0) === 0 ? 'good' : 'critical'
        },
        { 
          label: 'Sentiment', 
          value: report.metrics.sentiment_score?.toFixed(2) || '0.00',
          target: '>= 0.0',
          status: (report.metrics.sentiment_score || 0) >= 0 ? 'good' : 'critical'
        }
      ]

      const boxWidth = (pageWidth - 2 * margin - 9) / 4
      metricsData.forEach((item, idx) => {
        const xPos = margin + idx * (boxWidth + 3)
        const bgColor = item.status === 'good' ? '#d1fae5' : item.status === 'warning' ? '#fef3c7' : '#fee2e2'
        const borderColor = item.status === 'good' ? '#10b981' : item.status === 'warning' ? '#f59e0b' : '#ef4444'
        
        drawBox(xPos, yPos, boxWidth, 20, bgColor, borderColor)
        doc.setFontSize(7)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(75, 85, 99)
        doc.text(item.label, xPos + boxWidth / 2, yPos + 4, { align: 'center' })
        doc.setFontSize(14)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(31, 41, 55)
        doc.text(item.value, xPos + boxWidth / 2, yPos + 11, { align: 'center' })
        doc.setFontSize(6)
        doc.setFont('helvetica', 'italic')
        doc.setTextColor(107, 114, 128)
        doc.text(`Target: ${item.target}`, xPos + boxWidth / 2, yPos + 16, { align: 'center' })
      })
      yPos += 26
    }

    // Validation Flags Section (Hallucination Detection)
    if (report.validation_flags && report.validation_flags.length > 0) {
      if (yPos > 220) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('VALIDATION FLAGS (HALLUCINATION DETECTION)', yPos)

      doc.setFontSize(8)
      report.validation_flags.forEach((flag: any) => {
        if (yPos > 260) {
          doc.addPage()
          yPos = 20
        }

        const flagType = (flag.type || 'VALIDATION').toUpperCase()
        const severity = (flag.severity || 'HIGH').toLowerCase()
        let bgColor = '#fee2e2'
        let borderColor = '#ef4444'
        
        if (severity === 'medium') {
          bgColor = '#fef3c7'
          borderColor = '#f59e0b'
        }

        const boxHeight = 14
        drawBox(margin, yPos, pageWidth - 2 * margin, boxHeight, bgColor, borderColor)

        doc.setFont('helvetica', 'bold')
        doc.setTextColor(0, 0, 0)
        doc.text(`[${flagType}]`, margin + 2, yPos + 4)
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(7)
        doc.setTextColor(75, 85, 99)
        doc.text(`ID: ${sanitizeText(flag.product_id || 'N/A')}`, margin + 35, yPos + 4)
        doc.text(`Severity: ${severity.toUpperCase()}`, margin + 70, yPos + 4)

        doc.setFontSize(8)
        doc.setTextColor(31, 41, 55)
        const message = doc.splitTextToSize(sanitizeText(flag.message || ''), pageWidth - 2 * margin - 6)
        doc.text(message, margin + 2, yPos + 9)

        yPos += boxHeight + 2
      })
    }

    // Customer Support Analysis
    if (report.support_summary && Object.keys(report.support_summary).length > 0) {
      if (yPos > 240) {
        doc.addPage()
        yPos = 20
      }
      
      yPos = drawSectionHeader('CUSTOMER SUPPORT ANALYSIS', yPos)
      
      const supportData = []
      if (report.support_summary.sentiment !== undefined) {
        supportData.push({ label: 'Sentiment', value: report.support_summary.sentiment.toFixed(2) })
      }
      if (report.support_summary.velocity !== undefined) {
        supportData.push({ label: 'Complaint Velocity', value: `${report.support_summary.velocity.toFixed(1)}/10` })
      }
      if (report.support_summary.total_messages) {
        supportData.push({ label: 'Messages Analyzed', value: String(report.support_summary.total_messages) })
      }
      if (report.support_summary.complaint_count !== undefined) {
        supportData.push({ label: 'Complaints', value: String(report.support_summary.complaint_count) })
      }

      const boxWidth = (pageWidth - 2 * margin - 9) / 4
      supportData.forEach((item, idx) => {
        const xPos = margin + idx * (boxWidth + 3)
        drawBox(xPos, yPos, boxWidth, 12, '#f9fafb', '#e5e7eb')
        doc.setFontSize(8)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(55, 65, 81)
        doc.text(item.label, xPos + 2, yPos + 5)
        doc.setFontSize(9)
        doc.setFont('helvetica', 'normal')
        doc.text(item.value, xPos + 2, yPos + 9)
      })
      yPos += 18

      // Trending Topics
      if (report.support_summary.topics && report.support_summary.topics.length > 0) {
        yPos = drawSectionHeader('TRENDING TOPICS', yPos)
        doc.setFontSize(9)
        doc.setFont('helvetica', 'normal')
        doc.setTextColor(55, 65, 81)
        
        const topicsText = report.support_summary.topics.map((t: string) => sanitizeText(t)).join(', ')
        const lines = doc.splitTextToSize(topicsText, pageWidth - 2 * margin - 6)
        drawBox(margin, yPos - 2, pageWidth - 2 * margin, 8, '#fef3c7', '#f59e0b')
        doc.text(lines, margin + 3, yPos + 2)
        yPos += 10
      }

      // Classification Breakdown (calculate from classifications)
      if (report.support_summary.classifications && report.support_summary.classifications.length > 0) {
        const breakdown: Record<string, number> = {}
        report.support_summary.classifications.forEach((item: any) => {
          const type = item.type || 'Unknown'
          breakdown[type] = (breakdown[type] || 0) + 1
        })

        yPos = drawSectionHeader('MESSAGE CLASSIFICATION', yPos)
        const breakdownBoxWidth = (pageWidth - 2 * margin - 9) / 4
        Object.entries(breakdown).forEach(([type, count], idx) => {
          const xPos = margin + idx * (breakdownBoxWidth + 3)
          drawBox(xPos, yPos, breakdownBoxWidth, 12, '#f9fafb', '#e5e7eb')
          doc.setFontSize(7)
          doc.setFont('helvetica', 'bold')
          doc.setTextColor(55, 65, 81)
          doc.text(sanitizeText(type), xPos + 2, yPos + 5)
          doc.setFontSize(12)
          doc.setFont('helvetica', 'bold')
          doc.text(String(count), xPos + 2, yPos + 10)
        })
        yPos += 16
      }
    }

    // Catalog Issues with colored boxes
    if (report.catalog_issues && report.catalog_issues.length > 0) {
      if (yPos > 220) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('CATALOG HEALTH ANALYSIS', yPos)

      doc.setFontSize(8)
      report.catalog_issues.slice(0, 12).forEach((issue: any) => {
        if (yPos > 260) {
          doc.addPage()
          yPos = 20
        }

        // Determine color based on issue type
        const issueType = (issue.type || 'info').toLowerCase()
        let bgColor = '#eff6ff' // blue for info
        let borderColor = '#3b82f6'
        if (issueType === 'critical') {
          bgColor = '#fef2f2'
          borderColor = '#ef4444'
        } else if (issueType === 'warning') {
          bgColor = '#fffbeb'
          borderColor = '#f59e0b'
        }

        const boxHeight = issue.suggestion ? 18 : 12
        drawBox(margin, yPos, pageWidth - 2 * margin, boxHeight, bgColor, borderColor)

        // Issue header
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(0, 0, 0)
        doc.text(`[${(issue.type || 'NOTICE').toUpperCase()}]`, margin + 2, yPos + 4)
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(7)
        doc.setTextColor(75, 85, 99)
        doc.text(`ID: ${sanitizeText(issue.product_id || 'N/A')}`, margin + 30, yPos + 4)

        // Message
        doc.setFontSize(8)
        doc.setTextColor(31, 41, 55)
        const message = doc.splitTextToSize(sanitizeText(issue.message || issue.description || ''), pageWidth - 2 * margin - 6)
        doc.text(message, margin + 2, yPos + 8)

        // Suggestion
        if (issue.suggestion) {
          doc.setFontSize(7)
          doc.setTextColor(5, 150, 105)
          doc.setFont('helvetica', 'italic')
          const suggestion = doc.splitTextToSize(`> Fixed: ${sanitizeText(issue.suggestion)}`, pageWidth - 2 * margin - 6)
          doc.text(suggestion, margin + 2, yPos + 13)
        }

        yPos += boxHeight + 2
      })

      if (report.catalog_issues.length > 12) {
        doc.setFont('helvetica', 'italic')
        doc.setFontSize(8)
        doc.setTextColor(107, 114, 128)
        doc.text(`... and ${report.catalog_issues.length - 12} more issues`, margin, yPos)
        yPos += 8
      }
    }

    // Pricing Actions Table
    if (report.pricing_actions && report.pricing_actions.length > 0) {
      if (yPos > 200) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('PRICING ACTIONS', yPos)

      // Table header
      drawBox(margin, yPos, pageWidth - 2 * margin, 8, '#f9fafb', '#e5e7eb')
      doc.setFontSize(8)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(55, 65, 81)
      doc.text('Product', margin + 2, yPos + 5)
      doc.text('Current', margin + 60, yPos + 5)
      doc.text('Proposed', margin + 85, yPos + 5)
      doc.text('Final', margin + 115, yPos + 5)
      doc.text('Status', margin + 140, yPos + 5)
      yPos += 10

      // Table rows
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(7)
      report.pricing_actions.slice(0, 25).forEach((action: any, idx: number) => {
        if (yPos > 275) {
          doc.addPage()
          yPos = 20
        }

        // Alternating row colors
        if (idx % 2 === 0) {
          drawBox(margin, yPos - 3, pageWidth - 2 * margin, 6, '#f9fafb')
        }

        doc.setTextColor(75, 85, 99)
        const productName = sanitizeText((action.product_name || action.product_id || '').substring(0, 30))
        doc.text(productName, margin + 2, yPos)
        doc.text(`$${action.current_price?.toFixed(2) || '0.00'}`, margin + 60, yPos)
        doc.text(`$${action.proposed_price?.toFixed(2) || '0.00'}`, margin + 85, yPos)
        doc.text(`$${action.final_price?.toFixed(2) || '0.00'}`, margin + 115, yPos)
        
        // Status badge
        const status = action.status || 'UNKNOWN'
        const statusColors: any = {
          'APPROVED': { bg: '#d1fae5', text: '#065f46' },
          'BLOCKED': { bg: '#fee2e2', text: '#991b1b' },
          'LOCKED': { bg: '#fef3c7', text: '#92400e' },
          'ADJUSTED': { bg: '#dbeafe', text: '#1e40af' }
        }
        const colors = statusColors[status] || { bg: '#e5e7eb', text: '#374151' }
        drawBox(margin + 140, yPos - 3, 25, 5, colors.bg)
        doc.setFontSize(6)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(colors.text)
        doc.text(status, margin + 152.5, yPos, { align: 'center' })
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(7)

        yPos += 6
      })

      if (report.pricing_actions.length > 25) {
        yPos += 2
        doc.setFont('helvetica', 'italic')
        doc.setFontSize(8)
        doc.setTextColor(107, 114, 128)
        doc.text(`... and ${report.pricing_actions.length - 25} more actions`, margin, yPos)
        yPos += 8
      }
    }

    // Recommendations
    if (report.recommendations && report.recommendations.length > 0) {
      if (yPos > 230) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('RECOMMENDATIONS', yPos)

      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(55, 65, 81)
      report.recommendations.forEach((rec: string) => {
        if (yPos > 275) {
          doc.addPage()
          yPos = 20
        }
        drawBox(margin, yPos - 2, pageWidth - 2 * margin, 8, '#f9fafb', '#667eea')
        const lines = doc.splitTextToSize(`> ${sanitizeText(rec)}`, pageWidth - 2 * margin - 6)
        doc.text(lines, margin + 3, yPos + 2)
        yPos += 10
      })
    }

    // Warnings
    if (report.warnings && report.warnings.length > 0) {
      if (yPos > 230) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('WARNINGS', yPos)

      doc.setFontSize(9)
      doc.setFont('helvetica', 'normal')
      doc.setTextColor(127, 29, 29)
      report.warnings.forEach((warning: string) => {
        if (yPos > 275) {
          doc.addPage()
          yPos = 20
        }
        drawBox(margin, yPos - 2, pageWidth - 2 * margin, 8, '#fef2f2', '#ef4444')
        const lines = doc.splitTextToSize(`! ${sanitizeText(warning)}`, pageWidth - 2 * margin - 6)
        doc.text(lines, margin + 3, yPos + 2)
        yPos += 10
      })
    }

    // Merchant Locks
    if (report.merchant_locks && Object.keys(report.merchant_locks).length > 0) {
      if (yPos > 220) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('LOCKED PRODUCTS (MERCHANT OVERRIDES)', yPos)

      // Table header
      drawBox(margin, yPos, pageWidth - 2 * margin, 8, '#f9fafb', '#e5e7eb')
      doc.setFontSize(8)
      doc.setFont('helvetica', 'bold')
      doc.setTextColor(55, 65, 81)
      doc.text('Product ID', margin + 2, yPos + 5)
      doc.text('Reason', margin + 50, yPos + 5)
      doc.text('Status', margin + 130, yPos + 5)
      yPos += 10

      // Table rows
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(7)
      Object.entries(report.merchant_locks).forEach(([productId, lockInfo]: [string, any], idx: number) => {
        if (yPos > 275) {
          doc.addPage()
          yPos = 20
        }

        if (idx % 2 === 0) {
          drawBox(margin, yPos - 3, pageWidth - 2 * margin, 6, '#f9fafb')
        }

        doc.setTextColor(75, 85, 99)
        doc.text(sanitizeText(productId), margin + 2, yPos)
        doc.text(sanitizeText(lockInfo.reason || 'Manual override'), margin + 50, yPos)
        
        drawBox(margin + 130, yPos - 3, 25, 5, '#fef3c7')
        doc.setFontSize(6)
        doc.setFont('helvetica', 'bold')
        doc.setTextColor('#92400e')
        doc.text('LOCKED', margin + 142.5, yPos, { align: 'center' })
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(7)

        yPos += 6
      })
    }

    // Audit Log
    if (report.audit_log && report.audit_log.length > 0) {
      if (yPos > 220) {
        doc.addPage()
        yPos = 20
      }

      yPos = drawSectionHeader('AUDIT TRAIL', yPos)

      doc.setFontSize(8)
      report.audit_log.forEach((entry: any, idx: number) => {
        if (yPos > 270) {
          doc.addPage()
          yPos = 20
        }

        drawBox(margin, yPos, pageWidth - 2 * margin, 12, '#f9fafb', '#667eea')
        
        doc.setFont('helvetica', 'bold')
        doc.setTextColor(102, 126, 234)
        doc.text(`Step ${idx + 1}: ${sanitizeText(entry.action?.replace(/_/g, ' ').toUpperCase() || 'ACTION')}`, margin + 2, yPos + 4)
        
        doc.setFont('helvetica', 'normal')
        doc.setFontSize(7)
        doc.setTextColor(75, 85, 99)
        
        let detailY = yPos + 8
        if (entry.merchant_id) {
          doc.text(`Merchant: ${sanitizeText(entry.merchant_id)}`, margin + 2, detailY)
        }
        if (entry.flags_found !== undefined) {
          doc.text(`Flags: ${entry.flags_found}`, margin + 60, detailY)
        }
        if (entry.alert_level) {
          doc.text(`Alert: ${entry.alert_level}`, margin + 90, detailY)
        }

        doc.setFontSize(8)
        yPos += 14
      })
    }

    // Footer on all pages
    const pageCount = doc.getNumberOfPages()
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i)
      drawBox(0, 287, pageWidth, 10, '#f3f4f6')
      doc.setFontSize(7)
      doc.setFont('helvetica', 'italic')
      doc.setTextColor(107, 114, 128)
      doc.text(`Generated: ${new Date().toLocaleString()}`, margin, 292)
      doc.text(`Page ${i} of ${pageCount}`, pageWidth - margin - 20, 292)
    }

    // Save the PDF
    const timestamp = new Date().toISOString().split('T')[0]
    doc.save(`salla-operations-report-${timestamp}.pdf`)
  }

  return (
    <div className={styles.container}>
      {/* Loading Overlay */}
      {/* This ensures the user sees the dashboard "thinking" even if triggered from Chat */}
      {loading && (
        <div className={styles.loadingOverlay}>
          <div className={styles.spinner}></div>
          <p>🤖 AI Agents are analyzing your store...</p>
        </div>
      )}

      <header className={styles.header}>
        <h1>🏪 Salla Merchant Operations</h1>
        <p>Autonomous multi-agent system for merchant management</p>
      </header>

      <div className={styles.content}>
        <div className={styles.actionCard}>
          <h2>Daily Operations Check</h2>
          <p>Run the autonomous agent system to analyze your store operations</p>
          
          {/* File Upload Section */}
          <div className={styles.fileUploadSection}>
            <h3>📁 Upload Data Files (Optional)</h3>
            <p className={styles.uploadHint}>Upload CSV files or use default sample data</p>
            
            <div className={styles.fileInputsGrid}>
              <div className={styles.fileInputGroup}>
                <label htmlFor="products-file" className={uploadedFiles.products ? styles.fileUploaded : ''}>
                  <span className={styles.fileLabel}>
                    Products Catalog
                    {uploadedFiles.products && <span className={styles.uploadedCheck}> ✓</span>}
                  </span>
                  <span className={styles.fileName}>
                    {uploadedFiles.products ? uploadedFiles.products.name : 'No file selected'}
                  </span>
                </label>
                <input
                  id="products-file"
                  type="file"
                  accept=".csv"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload('products', e.target.files[0])}
                  className={styles.fileInput}
                />
              </div>

              <div className={styles.fileInputGroup}>
                <label htmlFor="messages-file" className={uploadedFiles.messages ? styles.fileUploaded : ''}>
                  <span className={styles.fileLabel}>
                    Customer Messages
                    {uploadedFiles.messages && <span className={styles.uploadedCheck}> ✓</span>}
                  </span>
                  <span className={styles.fileName}>
                    {uploadedFiles.messages ? uploadedFiles.messages.name : 'No file selected'}
                  </span>
                </label>
                <input
                  id="messages-file"
                  type="file"
                  accept=".csv"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload('messages', e.target.files[0])}
                  className={styles.fileInput}
                />
              </div>

              <div className={styles.fileInputGroup}>
                <label htmlFor="pricing-file" className={uploadedFiles.pricing ? styles.fileUploaded : ''}>
                  <span className={styles.fileLabel}>
                    Pricing Context
                    {uploadedFiles.pricing && <span className={styles.uploadedCheck}> ✓</span>}
                  </span>
                  <span className={styles.fileName}>
                    {uploadedFiles.pricing ? uploadedFiles.pricing.name : 'No file selected'}
                  </span>
                </label>
                <input
                  id="pricing-file"
                  type="file"
                  accept=".csv"
                  onChange={(e) => e.target.files?.[0] && handleFileUpload('pricing', e.target.files[0])}
                  className={styles.fileInput}
                />
              </div>
            </div>
            
            {(uploadedFiles.products || uploadedFiles.messages || uploadedFiles.pricing) && (
              <div className={styles.uploadSummary}>
                <span className={styles.uploadSummaryText}>
                  {[uploadedFiles.products, uploadedFiles.messages, uploadedFiles.pricing].filter(Boolean).length} of 3 files uploaded
                </span>
                <button 
                  onClick={() => setUploadedFiles({})}
                  className={styles.clearButton}
                  type="button"
                >
                  Clear All
                </button>
              </div>
            )}
          </div>

          <button 
            onClick={() => runOperationsCheck()}
            disabled={loading}
            className={styles.primaryButton}
          >
            {loading ? '⏳ Running...' : '▶️ Run Operations Check'}
          </button>
        </div>

        {error && (
          <div className={styles.errorCard}>
            <h3>❌ Error</h3>
            <p>{error}</p>
          </div>
        )}

        {report && (
          <div className={styles.reportCard}>
            <div className={styles.reportHeader}>
              <h2>📊 Operations Report</h2>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button 
                  onClick={exportToPDF}
                  className={styles.pdfButton}
                  title="Export to PDF"
                >
                  📄 Export PDF
                </button>
                <div 
                  className={styles.alertBadge}
                  style={{ backgroundColor: getAlertColor(report.alert_level) }}
                >
                  {report.alert_level || 'N/A'}
                </div>
              </div>
            </div>

            {report.status === 'FROZEN' && (
              <div className={styles.alertBox}>
                <h3>🚨 System Throttled</h3>
                <p>{report.alert_message}</p>
              </div>
            )}

            {report.throttle_mode_active && report.status !== 'FROZEN' && (
              <div className={styles.alertBox} style={{ backgroundColor: '#fef3c7', borderColor: '#f59e0b' }}>
                <h3>⚠️ Throttle Mode Active</h3>
                <p>System is operating in safety mode due to previous viral spike detection.</p>
              </div>
            )}

            {report.schema_validation_passed !== undefined && (
              <div className={styles.section} style={{ padding: '10px 20px', backgroundColor: '#f9fafb' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: 'bold' }}>Data Quality:</span>
                  {report.schema_validation_passed ? (
                    <span style={{ color: '#10b981' }}>✓ Valid</span>
                  ) : (
                    <span style={{ color: '#f59e0b' }}>
                      ⚠️ Validation Issues {report.retry_count ? `(${report.retry_count} retries)` : ''}
                    </span>
                  )}
                </div>
              </div>
            )}

            {report.summary && (
              <div className={styles.section}>
                <h3>📈 Summary</h3>
                <div className={styles.statsGrid}>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Total Products</span>
                    <span className={styles.statValue}>{report.summary.total_products}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Approved Changes</span>
                    <span className={styles.statValue}>{report.summary.approved_changes}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Blocked Changes</span>
                    <span className={styles.statValue}>{report.summary.blocked_changes}</span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Locked Products</span>
                    <span className={styles.statValue}>{report.summary.locked_products}</span>
                  </div>
                </div>
              </div>
            )}

            {report.metrics && (
              <div className={styles.section}>
                <h3>📊 Reliability Metrics</h3>
                <div className={styles.statsGrid}>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Pricing Pass Rate</span>
                    <span className={styles.statValue} style={{ 
                      color: (report.metrics.pricing_pass_rate || 0) >= 80 ? '#10b981' : '#f59e0b' 
                    }}>
                      {report.metrics.pricing_pass_rate?.toFixed(1) || '0.0'}%
                    </span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Automated Block Rate</span>
                    <span className={styles.statValue} style={{ 
                      color: (report.metrics.automated_block_rate || 0) <= 10 ? '#10b981' : '#f59e0b' 
                    }}>
                      {report.metrics.automated_block_rate?.toFixed(1) || '0.0'}%
                    </span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Hallucination Rate</span>
                    <span className={styles.statValue} style={{ 
                      color: (report.metrics.hallucination_rate || 0) === 0 ? '#10b981' : '#ef4444' 
                    }}>
                      {report.metrics.hallucination_rate?.toFixed(1) || '0.0'}%
                    </span>
                  </div>
                  <div className={styles.stat}>
                    <span className={styles.statLabel}>Sentiment Score</span>
                    <span className={styles.statValue} style={{ 
                      color: (report.metrics.sentiment_score || 0) >= 0 ? '#10b981' : '#ef4444' 
                    }}>
                      {report.metrics.sentiment_score?.toFixed(2) || '0.00'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {report.validation_flags && report.validation_flags.length > 0 && (
              <div className={styles.section}>
                <h3>🕵️ Validation Flags (Hallucination Detection)</h3>
                <div className={styles.issuesGrid}>
                  {report.validation_flags.map((flag: any, idx: number) => (
                    <div key={idx} className={`${styles.issueCard} ${styles[flag.severity?.toLowerCase() || 'high']}`}>
                      <div className={styles.issueHeader}>
                        <span className={styles.issueType}>{flag.type || 'VALIDATION'}</span>
                        {flag.product_id && <span className={styles.issueId}>ID: {flag.product_id}</span>}
                      </div>
                      <p className={styles.issueMessage}>{flag.message}</p>
                      {flag.severity && (
                        <div className={styles.issueSuggestion}>
                          <span className={styles.arrowIcon}>⚠️</span> 
                          Severity: <strong>{flag.severity}</strong>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {report.merchant_locks && Object.keys(report.merchant_locks).length > 0 && (
              <div className={styles.section}>
                <h3>🔒 Locked Products (Merchant Overrides)</h3>
                <div className={styles.tableContainer}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Product ID</th>
                        <th>Reason</th>
                        <th>Locked Date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(report.merchant_locks).map(([productId, lockInfo]: [string, any], idx: number) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 500 }}>{productId}</td>
                          <td>{lockInfo.reason || 'Manual override'}</td>
                          <td>{lockInfo.locked_at || 'N/A'}</td>
                          <td>
                            <span className={`${styles.statusBadge} ${styles.locked}`}>
                              LOCKED
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {report.support_summary && Object.keys(report.support_summary).length > 0 && (
              <div className={styles.section}>
                <h3>🎧 Customer Support Analysis</h3>
                <div className={styles.infoGrid}>
                  {report.support_summary.sentiment !== undefined && (
                    <p><strong>Sentiment:</strong> {report.support_summary.sentiment.toFixed(2)}</p>
                  )}
                  {report.support_summary.velocity !== undefined && (
                    <p><strong>Complaint Velocity:</strong> {report.support_summary.velocity.toFixed(1)}/10</p>
                  )}
                  {report.support_summary.total_messages && (
                    <p><strong>Messages Analyzed:</strong> {report.support_summary.total_messages}</p>
                  )}
                  {report.support_summary.complaint_count !== undefined && (
                    <p><strong>Complaints:</strong> {report.support_summary.complaint_count}</p>
                  )}
                </div>

                {/* Trending Topics Display */}
                {report.support_summary.topics && report.support_summary.topics.length > 0 && (
                  <div style={{ marginTop: '15px' }}>
                    <h4 style={{ fontSize: '14px', marginBottom: '8px', color: '#4b5563' }}>🔥 Trending Topics:</h4>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                      {report.support_summary.topics.map((topic: string, idx: number) => (
                        <span key={idx} style={{
                          backgroundColor: '#fef3c7',
                          border: '1px solid #f59e0b',
                          borderRadius: '15px',
                          padding: '5px 12px',
                          fontSize: '13px',
                          color: '#92400e',
                          fontWeight: '500'
                        }}>
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Dynamic Classification Breakdown */}
                {(classificationBreakdown || report.support_summary.breakdown) && (
                  <div style={{ marginTop: '15px' }}>
                    <h4 style={{ fontSize: '14px', marginBottom: '10px', color: '#4b5563' }}>📊 Message Classification:</h4>
                    <div className={styles.statsGrid}>
                      {Object.entries(classificationBreakdown || report.support_summary.breakdown).map(([type, count]: [string, any]) => (
                        <div key={type} className={styles.stat}>
                          <span className={styles.statLabel}>{type}</span>
                          <span className={styles.statValue}>{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {report.catalog_issues && report.catalog_issues.length > 0 && (
              <div className={styles.section}>
                <h3>📦 Catalog Health Analysis</h3>
                <div className={styles.issuesGrid}>
                  {report.catalog_issues.map((issue: any, idx: number) => (
                    <div key={idx} className={`${styles.issueCard} ${styles[issue.type?.toLowerCase() || 'info']}`}>
                      <div className={styles.issueHeader}>
                        <span className={styles.issueType}>{issue.type || 'NOTICE'}</span>
                        {issue.product_id && <span className={styles.issueId}>ID: {issue.product_id}</span>}
                        {issue.id && !issue.product_id && <span className={styles.issueId}>ID: {issue.id}</span>}
                      </div>
                      <p className={styles.issueMessage}>
                        {issue.message || issue.description || issue.issue || JSON.stringify(issue)}
                      </p>
                      {issue.suggestion && (
                        <div className={styles.issueSuggestion}>
                          <span className={styles.arrowIcon}>↳</span> 
                          Fixed: <strong>{issue.suggestion}</strong>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {report.pricing_actions && report.pricing_actions.length > 0 && (
              <div className={styles.section}>
                <h3>💰 Pricing Actions</h3>
                <div className={styles.tableContainer}>
                  <table className={styles.table}>
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Current</th>
                        <th>Proposed</th>
                        <th>Final</th>
                        <th>Cost</th>
                        <th>Margin</th>
                        <th>Status</th>
                        <th style={{ width: '30%' }}>Reasoning & Signals</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.pricing_actions.map((action: any, idx: number) => {
                        const cost = action.cost || 0
                        const finalPrice = action.final_price || 0
                        const margin = finalPrice > 0 ? ((finalPrice - cost) / finalPrice * 100) : 0
                        const marginColor = margin >= 30 ? '#10b981' : margin >= 15 ? '#f59e0b' : '#ef4444'
                        
                        return (
                          <tr key={idx}>
                            <td style={{ fontWeight: 500 }}>{action.product_name || action.product_id}</td>
                            <td>${action.current_price?.toFixed(2)}</td>
                            <td>${action.proposed_price?.toFixed(2)}</td>
                            <td style={{ fontWeight: 'bold' }}>${finalPrice.toFixed(2)}</td>
                            <td>${cost.toFixed(2)}</td>
                            <td style={{ color: marginColor, fontWeight: 'bold' }}>
                              {margin.toFixed(1)}%
                            </td>
                            <td>
                              <span className={`${styles.statusBadge} ${styles[action.status?.toLowerCase()]}`}>
                                {action.status}
                              </span>
                            </td>
                            <td>
                              <div className={styles.reasoningText}>
                                {action.reasoning || action.note || "No specific reasoning provided."}
                              </div>
                              
                              {action.signals_used && action.signals_used.length > 0 && (
                                <div className={styles.signalsContainer}>
                                  <span className={styles.signalsLabel}>Signals:</span>
                                  {action.signals_used.map((signal: string, sIdx: number) => (
                                    <span key={sIdx} className={styles.signalTag}>
                                      {signal}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {report.recommendations && report.recommendations.length > 0 && (
              <div className={styles.section}>
                <h3>💡 Recommendations</h3>
                <ul className={styles.list}>
                  {report.recommendations.map((rec: string, idx: number) => (
                    <li key={idx}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.warnings && report.warnings.length > 0 && (
              <div className={styles.section}>
                <h3>⚠️ Warnings</h3>
                <ul className={styles.list}>
                  {report.warnings.map((warning: string, idx: number) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {report.audit_log && report.audit_log.length > 0 && (
              <div className={styles.section}>
                <h3>📋 Audit Trail</h3>
                <div style={{ fontSize: '13px' }}>
                  <div style={{ 
                    display: 'grid', 
                    gap: '8px',
                    maxHeight: '300px',
                    overflowY: 'auto',
                    padding: '10px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '6px'
                  }}>
                    {report.audit_log.map((entry: any, idx: number) => (
                      <div 
                        key={idx} 
                        style={{ 
                          padding: '10px',
                          backgroundColor: '#ffffff',
                          borderLeft: '3px solid #667eea',
                          borderRadius: '4px',
                          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                          <span style={{ fontWeight: 'bold', color: '#667eea' }}>
                            {entry.action?.replace(/_/g, ' ').toUpperCase()}
                          </span>
                          <span style={{ fontSize: '11px', color: '#6b7280' }}>
                            Step {idx + 1}
                          </span>
                        </div>
                        {entry.merchant_id && (
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>
                            Merchant: {entry.merchant_id}
                          </div>
                        )}
                        {entry.flags_found !== undefined && (
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>
                            Flags Found: {entry.flags_found}
                          </div>
                        )}
                        {entry.alert_level && (
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>
                            Alert Level: <span style={{ 
                              color: entry.alert_level === 'RED' ? '#ef4444' : 
                                     entry.alert_level === 'YELLOW' ? '#f59e0b' : '#10b981',
                              fontWeight: 'bold'
                            }}>{entry.alert_level}</span>
                          </div>
                        )}
                        {entry.metrics && (
                          <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '5px' }}>
                            Metrics: Pass Rate {entry.metrics.pricing_pass_rate}%, 
                            Hallucinations {entry.metrics.hallucination_rate}%
                          </div>
                        )}
                        {entry.reason && (
                          <div style={{ fontSize: '12px', color: '#ef4444', marginTop: '5px' }}>
                            Reason: {entry.reason}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

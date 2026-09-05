/**
 * MRPL AI WORKBENCH - Enterprise Mock Data
 * 
 * Contains mock enterprise documents, sample user conversations,
 * and realistic technical AI markdown response templates.
 */

const MOCK_DATA = {
  // Realistic Enterprise Mock Documents
  INITIAL_DOCUMENTS: [
    {
      id: 'doc-001',
      title: 'MRPL Annual Report.pdf',
      type: 'PDF',
      size: '4.2 MB',
      updated: '2026-09-02',
      pages: 142,
      active: true,
      category: 'Finance & Compliance'
    },
    {
      id: 'doc-002',
      title: 'Refinery Safety Guidelines.pdf',
      type: 'PDF',
      size: '1.8 MB',
      updated: '2026-08-30',
      pages: 48,
      active: true,
      category: 'OISD Safety'
    },
    {
      id: 'doc-003',
      title: 'Piping Inspection Report.pdf',
      type: 'PDF',
      size: '850 KB',
      updated: '2026-08-28',
      pages: 12,
      active: true,
      category: 'Unit 4 Asset Integrity'
    },
    {
      id: 'doc-004',
      title: 'Vendor Evaluation.xlsx',
      type: 'XLSX',
      size: '320 KB',
      updated: '2026-08-20',
      pages: 4,
      active: false,
      category: 'Procurement'
    },
    {
      id: 'doc-005',
      title: 'Maintenance SOP.docx',
      type: 'DOCX',
      size: '1.2 MB',
      updated: '2026-08-15',
      pages: 26,
      active: false,
      category: 'Operations'
    },
    {
      id: 'doc-006',
      title: 'Equipment Inspection Images.zip',
      type: 'ZIP',
      size: '18.4 MB',
      updated: '2026-08-10',
      pages: 1,
      active: false,
      category: 'Inspection Visuals'
    }
  ],

  // Sample Recent Conversations
  INITIAL_CONVERSATIONS: [
    {
      id: 'chat-001',
      title: 'Inspection report summary',
      subtitle: 'Piping Inspection Report Unit-4 analysis',
      date: 'Today, 14:20',
      active: true,
      modelId: 'engineering-intelligence'
    },
    {
      id: 'chat-002',
      title: 'Vendor evaluation analysis',
      subtitle: 'Q3 Vendor scorecard & pricing comparison',
      date: 'Yesterday',
      active: false,
      modelId: 'general-assistant'
    },
    {
      id: 'chat-003',
      title: 'Safety compliance questions',
      subtitle: 'OISD-137 high-temperature permit rules',
      date: '2026-09-01',
      active: false,
      modelId: 'engineering-intelligence'
    },
    {
      id: 'chat-004',
      title: 'Maintenance procedure review',
      subtitle: 'Unit 4 Crude Distillation shutdown SOP',
      date: '2026-08-29',
      active: false,
      modelId: 'document-vision-analyst'
    }
  ],

  // Realistic AI Markdown Responses for Demo & Offline Mode
  RESPONSES: {
    INSPECTION: `### Technical Assessment — Unit 4 Piping & Safety Audit

**Document Context**: \`Piping Inspection Report.pdf\` & \`Refinery Safety Guidelines.pdf\`  
**Security Classification**: Confidential — Internal MRPL Use Only  
**Audit Reference**: \`MRPL-ENG-2026-8402\`

#### 1. Thickness Measurements & Degradation Analysis:
- **Line 4-HC-201 (Hydrocarbon Feed)**: Ultrasonic thickness test recorded **8.4 mm** (Minimum design threshold: **6.8 mm**). Status: **SATISFACTORY**.
- **Line 4-STM-104 (High Pressure Steam)**: Corrosion rate evaluated at **0.12 mm/year**. Estimated remaining service life: **7.5 years**.

> [!IMPORTANT]
> **Mandatory Safety Permit**: All maintenance activities on Line 4-HC-201 require a **Hot Work Permit Class-A** approved by the Chief Safety Officer, accompanied by continuous combustible gas detection monitoring.

#### 2. Action Items Summary Table:
| Component ID | Location | Technical Condition | Required Maintenance Action | Priority Level |
| :--- | :--- | :--- | :--- | :--- |
| **Flange V-402** | Unit 4 De-ethanizer | Spiral gasket weeping | Replace with 316L graphite gasket | **High** |
| **Pump P-401** | Feed Manifold | Vibration at 3.2 mm/s | Perform laser alignment check | **Medium** |
| **Line 4-STM** | Steam Header | Thermal insulation damage | Re-clad insulation jacket | **Low** |

\`\`\`bash
# MRPL Diagnostic Telemetry Command
$ mrpl-telemetry-cli --unit 4 --line 4-HC-201 --verify-integrity
[INFO] Querying local ChromaDB vector index...
[SUCCESS] Thickness: 8.4mm | Operating Pressure: 38.2 bar (Max Allowed: 42.5 bar)
\`\`\`

#### Referenced Vector Chunks:
- [Source: Piping Inspection Report.pdf — Page 4, Section 2.1]
- [Source: Refinery Safety Guidelines.pdf — Page 18, Section 5.4]`,

    SAFETY: `### Safety & Operating Procedure Compliance (OISD Standards)

**Document Context**: \`Refinery Safety Guidelines.pdf\`  
**Compliance Standard**: OISD-137 / OISD-105  

#### 1. High-Temperature Work Permit Requirements:
1. **Isolation Verification**: Positive isolation via blind insertion mandatory for all lines exceeding **60°C** or **5.0 bar**.
2. **Gas Free Certificate**: Continuous oxygen (20.9%) and LEL testing (<1%) prior to entry into confined vessel spaces.
3. **PPE Protocols**: Aluminized thermal suits, SCBA units, and double-gloved leather safety wear mandatory.

#### 2. Emergency Response Hierarchy:
1. Trigger local unit ESD (Emergency Shutdown Button).
2. Contact Control Room Extension **#4444** (Refinery Emergency Hotline).
3. Notify On-Duty Fire Officer and initiate N2 purge.

- [Source: Refinery Safety Guidelines.pdf — Page 12, Clause 3.2]`,

    VENDOR: `### Vendor Evaluation & Procurement Analysis Matrix

**Document Context**: \`Vendor Evaluation.xlsx\` & \`MRPL Annual Report.pdf\`  

#### Summary of Supplier Performance Scorecard (Q3):
| Vendor Name | Equipment Scope | Financial Compliance | Delivery On-Time % | Quality Score (100) | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **L&T Heavy Engineering** | Valves & Fittings | Compliant | 96.5% | **94 / 100** | **Preferred Supplier** |
| **BHEL Hydro Systems** | High Pressure Pumps | Compliant | 88.0% | **87 / 100** | Approved |
| **Kirloskar Brothers** | Utility Impellers | Under Review | 91.2% | **81 / 100** | Conditional |

- [Source: Vendor Evaluation.xlsx — Sheet 1, Cell B4:F12]`,

    DEFAULT: `### MRPL AI Workbench Analysis

**Selected Engine**: Engineering Intelligence (\`qwen2.5-coder:7b\`)  
**Deployment Mode**: Offline On-Premise PSU Network  

#### Synthesis Result:
The query has been executed against selected internal document indices. All extracted data complies with MRPL refinery documentation standards.

1. **System Status**: Active ChromaDB vector index loaded with **3,420 chunks**.
2. **Execution Integrity**: Zero external cloud requests executed. 100% confidential internal processing.

\`\`\`python
# Sample RAG Query Payload Structure
request_payload = {
    "message": "User query string",
    "model": "qwen2.5-coder:7b",
    "conversation_id": "local-demo-session",
    "document_ids": ["doc-001", "doc-002", "doc-003"],
    "stream": True
}
\`\`\`

Specify document section parameters if further granular extraction is required.`
  }
};

if (typeof window !== 'undefined') {
  window.MOCK_DATA = MOCK_DATA;
}

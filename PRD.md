1. บริบทและโจทย์ปัญหา (Context & Problem Statement)

กระบวนการเบิกจ่ายค่ารักษาพยาบาลระหว่างโรงพยาบาล (ผ่านระบบ HIS) กับผู้จ่ายเงิน (Payer ทั้งภาครัฐและเอกชน) เผชิญกับคอขวดเชิงโครงสร้างจากความต่างของมาตรฐานข้อมูลและการบูรณาการแบบ Point-to-Point ส่งผลให้อัตราการปฏิเสธการเคลม (Reject Rate) สูง และเกิดภาระงานสะสมในกระบวนการตั้งหนี้และรับหนี้ (AR)

Claim Lifecycle: ตรวจสอบสิทธิ์ (Eligibility) -> ขออนุมัติล่วงหน้า (Pre-authorization) → รักษาพยาบาล -> ส่งข้อมูล Settlement -> การบริหารลูกหนี้ (AR)
Core Pain Point: บริษัทประกันเอกชนขาดมาตรฐานข้อมูลกลาง ทำให้โรงพยาบาลต้องสร้างการเชื่อมต่อแบบ One-to-One หรือใช้ระบบ Portal เฉพาะของแต่ละค่าย ขาดการตรวจสอบความถูกต้องอัตโนมัติก่อนส่งข้อมูลจริง

2. ขอบเขตสถาปัตยกรรมระบบ (Engineering Scope & Architecture Requirements) ให้นิสิตออกแบบและพัฒนาแพลตฟอร์มกลาง (Middleware/API Gateway) ที่มีสถาปัตยกรรมครอบคลุม 3 เลเยอร์หลัก ดังนี้:

Layer 1: High-Throughput Data Normalization Engine
แปลงข้อมูลดิบจาก HIS (รองรับรูปแบบที่หลากหลาย เช่น HL7 v2, Custom JSON/XML, หรือ Direct DB Extraction) ให้เป็น Canonical Data Model
ออกแบบระบบรองรับปริมาณธุรกรรมสูง (High Concurrency & Throughput) ช่วงเวลาพีคของโรงพยาบาล
Layer 2: Automated Business Logic & Clinical Validation Engine
ตรวจสอบความถูกต้องของเงื่อนไขการเบิกจ่ายอัตโนมัติก่อนส่งต่อให้ Payer (Pre-submission Validation)
ตรวจสอบความสอดคล้องทางคลินิกเบื้องต้น เช่น ความถูกต้องของรหัสโรค (ICD-10-TM), รหัสยาและเวชภัณฑ์มาตรฐานไทย (TMT), และความครบถ้วนของข้อมูลเวชระเบียนที่บังคับใช้
Layer 3: Localized Context & Rule Engine
จัดการกฎระเบียบเฉพาะบริบทประเทศไทย เช่น รูปแบบการแปลงศักราช (พ.ศ./ค.ศ.), รหัสสิทธิการรักษาภาครัฐ (บัตรทอง, สวัสดิการข้าราชการ, ประกันสังคม), และ Dynamic Rules ของแต่ละบริษัทประกันเอกชนที่เปลี่ยนแปลงบ่อย

3. เกณฑ์การส่งมอบและวัดผล Solution (Deliverables & Evaluation Metrics)

Architecture Design Document: แผนผังระบบ (System Architecture) และ API Specification (แนะนำให้ใช้มาตรฐาน FHIR หรือ OpenAPI)
Core Implementation: โค้ดต้นทางของระบบ 3 เลเยอร์ที่สามารถทำงานร่วมกันได้จริง
Evaluation Metrics:
ลด Reject Rate ที่เกิดจากรูปแบบข้อมูลผิดพลาดและความไม่ครบถ้วนลงได้ไม่น้อยกว่า 50% ในชุดข้อมูลทดสอบ
ระยะเวลาประมวลผล (Processing Latency) ต่อ 1 Claim Transaction ต้องอยู่ในเกณฑ์ที่เหมาะสมสำหรับการใช้งานจริงในโรงพยาบาล
รองรับการเพิ่ม Payer รายใหม่ผ่าน Plugin-based หรือ Config-driven โดยไม่ต้องแก้ไขโค้ดส่วน Core Engine

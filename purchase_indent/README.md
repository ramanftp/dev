# Purchase Indent 


### Configuration
To assign permissions:
1. Navigate to `Settings → Users & Companies → Groups`
2. Locate either:
   - "Purchase Indent Manager" group
   - "Purchase Indent User" group
3. Assign users to appropriate groups


#### Purchase Indent Manager (Full Access)
- **Actions**:
  - Submit indents for approval
  - Approve/reject indents
  - Cancel indents
  - Generate purchase orders
  - Access all reporting

#### Purchase Indent User (Restricted Access)
- **Actions**:
  - Create new indents
  - Edit own draft indents
  - Submit own indents for approval
  - View status of own indents
- **Restrictions**:
  - Cannot approve/reject indents
  - Cannot delete indents after submission
  - Cannot generate purchase orders

## Purpose  
creating and managing Purchase Indents in the Odoo system, which serve as internal requests for procurement of goods/services before generating formal Purchase Orders.


## Roles & Responsibilities  
- **Requester**: Initiates the indent request  
- **Technical Approver**: Reviews and approves/rejects the indent  
- **Procurement Team**: Converts approved indents to Purchase Orders  

## 1. Purchase Indent Creation

### 1.1 Initiate New Indent  
1. Navigate to: `Purchase Indents → Create`  
2. System auto-generates a unique reference number  
3. Fill in mandatory fields:  
   - Project  
   - Department  
   - Request Date (defaults to current date)  
   - Requester (auto-populated with current user)  

### 1.2 Add Line Items  
1. Click "Add a line" in the Items section  
2. For each item:  
   - Select Product (required)  
   - Description auto-populates but can be modified  
   - Enter Quantity (defaults to 1)  
   - Unit of Measure auto-populates from product  
   - Verify/select Vendor (required before submission)  
   - Unit Price auto-populates from product cost but can be modified  
   - Subtotal calculates automatically (Quantity × Unit Price)  

### 1.3 Save Draft  
- Click "Save" to store as draft  
- Draft indents can be edited until submission  

## 2. Indent Submission & Approval Workflow  

### 2.1 Submit for Approval  
1. Verify all line items are complete  
2. Ensure all products have vendors assigned  
3. Click "Submit" button  
4. System validates:  
   - At least one line item exists  
   - All products have vendors  
5. Status changes to "Waiting Approval"  

### 2.2 Technical Approval  
1. Technical approver reviews indent  
2. Options:  
   - **Approve**:  
     - Click "Approve"  
     - System records approver and timestamp  
     - Status changes to "Approved"  
   - **Reject**:  
     - Click "Reject"  
     - Enter rejection reason in pop-up wizard  
     - Status changes to "Rejected"  
     - Requester notified  

### 2.3 Additional Statuses  
- **Cancelled**: Can be set by authorized users to abort the process  
- **Draft**: Editable state before submission  

## 3. Purchase Order Generation  

### 3.1 Create Purchase Orders  
1. From approved indent, click "Create Purchase Orders"  
2. System:  
   - Groups items by vendor  
   - Checks for existing draft RFQs for same vendor/project  
   - Creates new RFQs or updates existing ones:  
     - New RFQ: Creates complete purchase order  
     - Existing RFQ: Adds new lines or updates quantities  
   - Maintains origin tracking with indent reference  
   - Links generated POs to the indent record  

### 3.2 View Generated POs  
- Approved indent shows count of linked POs  
- Click PO count to view list of generated purchase orders  

## 4. Special Cases & Validations  

### 4.1 Vendor Requirements  
- All products must have assigned vendors before:  
  - Submitting for approval  
  - Generating purchase orders  
- System prevents submission/PO generation if vendors missing  

### 4.2 Price Calculations  
- Unit prices default to product standard cost  
- Subtotals calculate automatically  
- Prices can be manually overridden before submission  

## 5. Reporting & Tracking  

### 5.1 Audit Trail  
- System tracks:  
  - Creation date/user  
  - Submission date  
  - Approval/rejection details  
  - PO generation history  

### 5.2 Document Reference  
- All generated POs include indent reference in their origin field  
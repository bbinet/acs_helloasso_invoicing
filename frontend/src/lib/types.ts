export interface Member {
  id: number;
  firstname: string;
  lastname: string;
  email: string;
  company?: string;
  activities: string[];
  order_date: string;
  ea: boolean;
  invoice_generated: boolean;
  invoice_date?: string;
  email_sent: boolean;
  email_date?: string;
  email_error?: boolean;
}

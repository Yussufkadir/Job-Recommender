export type ApplicationStatus = 'saved' | 'applied' | 'interview' | 'offer' | 'rejected';

export interface Application {
    id: number;
    user_id: number;
    job_title: string;
    company: string;
    job_url?: string;
    status: ApplicationStatus;
    notes?: string;
    created_at: string;
    updated_at: string;
}

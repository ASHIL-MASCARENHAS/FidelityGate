'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { WorkspaceApp } from '@/components/workspace/WorkspaceApp';

export default function WorkspacePage() {
  const router = useRouter();

  const handleBackToLanding = () => {
    router.push('/');
  };

  return <WorkspaceApp onBackToLanding={handleBackToLanding} />;
}

import React from 'react';
import LeftTelemetryPanels from './LeftTelemetryPanels';
import RadialNetworkTopology from './RadialNetworkTopology';
import RightAssurancePanels from './RightAssurancePanels';

export default function AryakaOverviewDashboard({
  scenarios = {},
  selectedScenarioKey,
  onSelectScenario,
  onTriggerDiagnostic,
  investigationResult
}) {
  const currentScenario = scenarios[selectedScenarioKey] || scenarios.wan_congestion;
  const report = investigationResult?.gate?.report;

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 p-1 select-none">
      {/* Left Column (3 of 12 cols in xl screens) */}
      <div className="xl:col-span-3">
        <LeftTelemetryPanels report={report} scenario={currentScenario} />
      </div>

      {/* Center Hero Column: Radial Network Topology (6 of 12 cols in xl screens) */}
      <div className="xl:col-span-6">
        <RadialNetworkTopology
          onSelectScenario={onSelectScenario}
          onTriggerDiagnostic={onTriggerDiagnostic}
          selectedScenarioKey={selectedScenarioKey}
        />
      </div>

      {/* Right Column: Threats & Flows (3 of 12 cols in xl screens) */}
      <div className="xl:col-span-3">
        <RightAssurancePanels onSelectScenario={onSelectScenario} />
      </div>
    </div>
  );
}

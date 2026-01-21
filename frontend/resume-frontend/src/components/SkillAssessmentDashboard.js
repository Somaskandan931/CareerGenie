import React from 'react';

const SkillAssessmentDashboard = ({ resumeSkills = [], jobSkills = [], comparison = null }) => {
  if (!comparison || !resumeSkills.length || !jobSkills.length) {
    return null;
  }

  // Calculate category scores
  const getCategoryScore = (category) => {
    const matched = comparison.matched_skills?.filter(s => s.category === category).length || 0;
    const total = jobSkills.filter(s => s.category === category).length || 0;
    return total > 0 ? (matched / total) * 100 : 0;
  };

  const categories = ['Programming', 'Frameworks', 'Databases', 'Cloud', 'Tools'];

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 Your Skill Assessment</h2>

      {/* Overall Score */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Overall Match</p>
            <p className="text-4xl font-bold text-blue-600">
              {Math.round(comparison.overall_match || 0)}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Skills Matched</p>
            <p className="text-2xl font-semibold text-gray-700">
              {comparison.matched_skills?.length || 0} / {jobSkills.length}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4 bg-gray-200 rounded-full h-4 overflow-hidden">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-full transition-all duration-500"
            style={{ width: `${comparison.overall_match || 0}%` }}
          />
        </div>
      </div>

      {/* Skill Categories */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {categories.map((category) => {
          const score = getCategoryScore(category);
          const color = score >= 80 ? 'green' : score >= 50 ? 'yellow' : 'red';

          return (
            <div key={category} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-700">{category}</h3>
                <span className={`text-${color}-600 font-bold`}>{Math.round(score)}%</span>
              </div>
              <div className="bg-gray-200 rounded-full h-2">
                <div
                  className={`bg-${color}-500 h-full rounded-full transition-all`}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Matched Skills */}
      {comparison.matched_skills && comparison.matched_skills.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-green-500 mr-2">✓</span>
            Your Strong Skills ({comparison.matched_skills.length})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {comparison.matched_skills.map((skill, idx) => (
              <div
                key={idx}
                className="bg-green-50 border border-green-200 rounded-lg p-3 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium text-green-900 text-sm">{skill.skill || skill}</p>
                    {skill.resume_level && (
                      <p className="text-xs text-green-700 mt-1">
                        {skill.resume_level}
                        {skill.years_experience > 0 && ` • ${skill.years_experience}y`}
                      </p>
                    )}
                  </div>
                  {skill.status === 'qualified' && (
                    <span className="text-green-500 text-xl">★</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Gaps */}
      {comparison.skill_gaps && comparison.skill_gaps.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-orange-500 mr-2">⚠</span>
            Skills to Develop ({comparison.skill_gaps.length})
          </h3>
          <div className="space-y-3">
            {comparison.skill_gaps.map((gap, idx) => (
              <div
                key={idx}
                className={`border-l-4 rounded-r-lg p-4 ${
                  gap.gap_severity === 'critical'
                    ? 'bg-red-50 border-red-500'
                    : 'bg-orange-50 border-orange-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900">{gap.skill}</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Your level: <span className="font-medium">{gap.resume_level || 'None'}</span>
                      {' → '}
                      Required: <span className="font-medium">{gap.required_level || 'Intermediate'}</span>
                    </p>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    gap.gap_severity === 'critical'
                      ? 'bg-red-200 text-red-800'
                      : 'bg-orange-200 text-orange-800'
                  }`}>
                    {gap.gap_severity || 'moderate'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Bonus Skills */}
      {comparison.bonus_skills && comparison.bonus_skills.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <span className="text-blue-500 mr-2">🌟</span>
            Bonus Skills ({comparison.bonus_skills.length})
          </h3>
          <div className="flex flex-wrap gap-2">
            {comparison.bonus_skills.map((skill, idx) => (
              <span
                key={idx}
                className="bg-blue-100 text-blue-800 px-3 py-2 rounded-full text-sm font-medium border border-blue-300"
              >
                {skill.skill || skill} {skill.level && `• ${skill.level}`}
              </span>
            ))}
          </div>
          <p className="text-sm text-gray-600 mt-3">
            These additional skills make you stand out from other candidates!
          </p>
        </div>
      )}

      {/* Action Recommendation */}
      <div className="mt-6 bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h4 className="font-semibold text-purple-900 mb-2">💡 Quick Recommendation</h4>
        <p className="text-sm text-purple-800">
          {(comparison.overall_match || 0) >= 80
            ? "Excellent match! Apply immediately and highlight your matching skills."
            : (comparison.overall_match || 0) >= 60
            ? "Good match! Focus on showcasing your strengths and be prepared to discuss skill gaps."
            : "Consider upskilling in critical areas before applying, or target more entry-level positions."}
        </p>
      </div>
    </div>
  );
};

export default SkillAssessmentDashboard;
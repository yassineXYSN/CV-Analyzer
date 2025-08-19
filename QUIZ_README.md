# Quiz Functionality - CV Analyzer Pro

## Overview

The quiz functionality has been successfully integrated into the CV Analyzer Pro project. This feature allows the system to automatically generate QCM (Multiple Choice Questions) quizzes tailored to job requirements and candidate skills, with automatic scoring and evaluation.

## Features

### 🎯 **Automatic Quiz Generation**
- Generates QCM questions based on job requirements and candidate skills
- Uses DeepSeek AI model for intelligent question generation
- Supports different difficulty levels (facile, moyen, difficile)
- Configurable number of questions (default: 10)

### 📊 **Smart Evaluation System**
- Automatic scoring and evaluation
- Category-based scoring (technical, behavioral, cultural)
- Detailed feedback with explanations
- Performance tracking over time

### 🎨 **Modern UI/UX**
- Interactive quiz interface with progress tracking
- Real-time timer and progress bar
- Beautiful results display with category breakdown
- Responsive design for all devices

## Technical Implementation

### Database Models

#### Quiz Model
```python
class Quiz(Base):
    __tablename__ = "quiz"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    job_title = Column(String)
    difficulty = Column(String)
    questions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    candidate_id = Column(Integer, ForeignKey("profile_candidat.id"))
```

#### QuizAttempt Model
```python
class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quiz.id"))
    candidate_id = Column(Integer, ForeignKey("profile_candidat.id"))
    answers = Column(JSON)
    total_score = Column(Float)
    category_scores = Column(JSON)
    detailed_results = Column(JSON)
    completed_at = Column(DateTime, default=datetime.utcnow)
```

### API Endpoints

#### Generate Quiz
```http
POST /generate-quiz
Content-Type: application/json

{
    "candidate_id": 1,
    "job_title": "Développeur Full Stack",
    "num_questions": 10
}
```

#### Submit Quiz
```http
POST /submit-quiz
Content-Type: application/json

{
    "quiz_id": 1,
    "candidate_id": 1,
    "answers": {
        1: "A",
        2: "B",
        3: "C"
    }
}
```

#### Get Quiz History
```http
GET /quiz-history/{candidate_id}
```

#### Get Quiz Statistics
```http
GET /quiz-stats/{quiz_id}
```

### Web Routes

#### Take Quiz
```http
GET /take-quiz/{candidate_id}
```

#### View Results
```http
GET /quiz-results/{attempt_id}
```

## Integration Points

### 1. CV Analysis Results
After CV analysis, a "Passer le QCM" button appears on the results page, allowing candidates to take a quiz based on their profile.

### 2. Job-Specific Questions
The system automatically maps job titles to required skills:
- **Développeur**: Python, JavaScript, SQL, Git, API
- **Data Scientist**: Python, R, SQL, Machine Learning, Statistics
- **DevOps**: Linux, Docker, Kubernetes, CI/CD, Cloud
- And more...

### 3. AI-Powered Generation
Uses DeepSeek model to generate contextual questions:
- Technical questions based on required skills
- Behavioral questions for soft skills assessment
- Cultural fit questions for company alignment

## Usage Flow

1. **CV Upload & Analysis**: User uploads CV and gets analysis
2. **Quiz Generation**: System generates personalized QCM based on job requirements
3. **Quiz Taking**: User answers questions with interactive interface
4. **Automatic Evaluation**: System scores answers and provides detailed feedback
5. **Results Display**: Comprehensive results with category breakdown
6. **History Tracking**: All attempts are stored for progress tracking

## Configuration

### Environment Variables
```bash
# DeepSeek API Configuration
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=your_api_key_here
```

### Quiz Settings
- **Default Questions**: 10
- **Question Types**: technique, comportemental, culturel
- **Scoring**: Percentage-based with category breakdown

## Testing

Run the test script to verify functionality:
```bash
python test_quiz.py
```

This will test:
- Quiz generation
- Quiz submission
- Results evaluation
- History retrieval

## Files Added/Modified

### New Files
- `quiz_generator.py` - AI-powered quiz generation
- `quiz_service.py` - Business logic for quiz operations
- `templates/client-dep/quiz.html` - Quiz interface
- `templates/client-dep/quiz_results.html` - Results display
- `test_quiz.py` - Test script
- `QUIZ_README.md` - This documentation

### Modified Files
- `models.py` - Added Quiz and QuizAttempt models
- `main.py` - Added quiz endpoints and routes
- `templates/client-dep/result.html` - Added quiz button
- `requirements.txt` - Added requests dependency

## Benefits

### For Candidates
- **Personalized Assessment**: Questions tailored to their skills and job requirements
- **Immediate Feedback**: Instant scoring and detailed explanations
- **Progress Tracking**: Historical performance data
- **Skill Validation**: Objective assessment of technical and soft skills

### For Recruiters
- **Automated Screening**: Reduces manual evaluation time
- **Standardized Assessment**: Consistent evaluation criteria
- **Detailed Analytics**: Category-based performance insights
- **Efficient Filtering**: Quick identification of top candidates

### For the System
- **Scalable**: Handles multiple candidates simultaneously
- **Intelligent**: AI-powered question generation
- **Flexible**: Configurable difficulty and question count
- **Integrated**: Seamless workflow from CV analysis to quiz

## Future Enhancements

1. **Advanced Analytics**: Detailed performance analytics and trends
2. **Custom Question Banks**: Allow recruiters to add custom questions
3. **Multi-language Support**: Support for different languages
4. **Video Questions**: Integration with video interview questions
5. **Collaborative Scoring**: Multiple evaluators for complex roles
6. **Adaptive Difficulty**: Dynamic difficulty adjustment based on performance

## Troubleshooting

### Common Issues

1. **API Connection Error**
   - Verify DeepSeek API key in environment variables
   - Check internet connectivity
   - Ensure API endpoint is accessible

2. **Quiz Generation Fails**
   - Check candidate profile exists in database
   - Verify job title mapping in quiz service
   - Review API response for errors

3. **Database Errors**
   - Ensure database tables are created
   - Check foreign key relationships
   - Verify database connection

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DEBUG_QUIZ=true
```

## Support

For technical support or feature requests, please refer to the main project documentation or create an issue in the project repository. 
"""Tests for Client Classifier Agent"""

from src.agents.client_classifier import ClientClassifier
from src.config.template_rules import ClientType
from src.models.client_brief import ClientBrief


class TestClientClassifierInit:
    """Test ClientClassifier initialization"""

    def test_init_creates_classifier(self):
        """Test creating a classifier instance"""
        classifier = ClientClassifier()
        assert classifier is not None


class TestClassifyClient:
    """Test classify_client method"""

    def test_classify_b2b_saas(self):
        """Test classifying B2B SaaS client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="TechCo",
            business_description="We build SaaS software platforms for enterprise teams and organizations",
            ideal_customer="CTOs and VPs at B2B companies",
            main_problem_solved="API integration and technology solutions",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.B2B_SAAS
        assert confidence > 0.15  # Above threshold

    def test_classify_agency(self):
        """Test classifying agency client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Creative Agency",
            business_description="Marketing agency providing creative services and campaign strategy",
            ideal_customer="Brands and companies needing marketing support",
            main_problem_solved="Creative marketing campaigns for clients",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.AGENCY
        assert confidence > 0.15

    def test_classify_coach_consultant(self):
        """Test classifying coach/consultant client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Success Coach",
            business_description="Business coach providing consulting and mentoring to transform professionals",
            ideal_customer="Entrepreneurs and executives seeking guidance",
            main_problem_solved="Leadership training and advisor services",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.COACH_CONSULTANT
        assert confidence > 0.15

    def test_classify_creator_founder(self):
        """Test classifying creator/founder client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Startup Founder",
            business_description="Indie hacker building a bootstrapped startup",
            ideal_customer="Followers and community members",
            main_problem_solved="Launched solopreneur platform for creators",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.CREATOR_FOUNDER
        assert confidence > 0.15

    def test_classify_real_estate(self):
        """Test classifying real estate client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Real Estate Pro",
            business_description="Real estate broker specializing in residential properties and commercial listings",
            ideal_customer="Home buyers, sellers, and investors",
            main_problem_solved="Finding the perfect homes for families",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.REAL_ESTATE
        assert confidence > 0.15

    def test_classify_restaurant_hospitality(self):
        """Test classifying restaurant/hospitality client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Fine Dining",
            business_description="Upscale restaurant offering fine cuisine and exceptional hospitality",
            ideal_customer="Food lovers and diners seeking quality dining experiences",
            main_problem_solved="Providing memorable dining and catering services",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.RESTAURANT_HOSPITALITY
        assert confidence > 0.15

    def test_classify_ecommerce_retail(self):
        """Test classifying e-commerce/retail client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Fashion Boutique",
            business_description="Online store selling fashion clothing and accessories",
            ideal_customer="Fashion lovers and online shoppers",
            main_problem_solved="Curated products for modern retail consumers",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.ECOMMERCE_RETAIL
        assert confidence > 0.15

    def test_classify_healthcare(self):
        """Test classifying healthcare client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Health Clinic",
            business_description="Medical clinic providing healthcare services and patient care",
            ideal_customer="Patients and families in the community",
            main_problem_solved="Quality wellness and doctor services",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.HEALTHCARE
        assert confidence > 0.15

    def test_classify_nonprofit(self):
        """Test classifying nonprofit client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Community Foundation",
            business_description="Nonprofit charity organization supporting community causes and social impact",
            ideal_customer="Donors and volunteers passionate about advocacy",
            main_problem_solved="Advancing our mission to help communities",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.NONPROFIT
        assert confidence > 0.15

    def test_classify_legal(self):
        """Test classifying legal client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Law Firm",
            business_description="Legal practice providing attorney services and litigation counsel",
            ideal_customer="Clients and businesses needing legal representation",
            main_problem_solved="Expert legal advocacy for individuals and companies",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.LEGAL
        assert confidence > 0.15

    def test_classify_financial_services(self):
        """Test classifying financial services client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Wealth Advisors",
            business_description="Financial advisor providing investment and retirement planning",
            ideal_customer="Investors, retirees, and high-net-worth families",
            main_problem_solved="Tax planning and wealth management for entrepreneurs",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.FINANCIAL_SERVICES
        assert confidence > 0.15

    def test_classify_home_services(self):
        """Test classifying home services client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Home Improvement Co",
            business_description="Contractor specializing in home improvement, renovation and remodeling",
            ideal_customer="Homeowners and property owners",
            main_problem_solved="Quality construction and HVAC services for families",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.HOME_SERVICES
        assert confidence > 0.15

    def test_classify_education(self):
        """Test classifying education client"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Online Academy",
            business_description="Education platform offering online courses and training for learning",
            ideal_customer="Students and professionals seeking career development",
            main_problem_solved="Quality university-level education for learners",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.EDUCATION
        assert confidence > 0.15

    def test_classify_unknown_low_confidence(self):
        """Test classifying as UNKNOWN when confidence is too low"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Mystery Business",
            business_description="We do various things",
            ideal_customer="People who need help",
            main_problem_solved="General solutions",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.UNKNOWN
        assert confidence < 0.15  # Below threshold

    def test_classify_unknown_no_keywords(self):
        """Test classifying as UNKNOWN when no keywords match"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Unique Business",
            business_description="Completely novel industry with no standard keywords",
            ideal_customer="Special segment not in database",
            main_problem_solved="Unique problem nobody else has",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.UNKNOWN

    def test_classify_handles_empty_fields(self):
        """Test classification with minimal/empty fields"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Test Co",
            business_description="",
            ideal_customer="",
            main_problem_solved="",
        )

        client_type, confidence = classifier.classify_client(brief)

        # Should not crash, should return UNKNOWN
        assert client_type == ClientType.UNKNOWN
        assert confidence == 0.0

    def test_classify_case_insensitive(self):
        """Test that classification is case-insensitive"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="TECH CO",
            business_description="SAAS PLATFORM FOR ENTERPRISE COMPANIES",
            ideal_customer="CTO AND VP OF TECHNOLOGY",
            main_problem_solved="SOFTWARE SOLUTIONS FOR B2B TEAMS",
        )

        client_type, confidence = classifier.classify_client(brief)

        assert client_type == ClientType.B2B_SAAS
        assert confidence > 0.15

    def test_confidence_score_increases_with_more_keywords(self):
        """Test that confidence increases with more keyword matches"""
        classifier = ClientClassifier()

        # Brief with few keywords
        brief_low = ClientBrief(
            company_name="Tech Startup",
            business_description="Software platform",
            ideal_customer="Companies",
            main_problem_solved="Technology",
        )

        # Brief with many keywords
        brief_high = ClientBrief(
            company_name="Enterprise SaaS",
            business_description="SaaS software platform with API and B2B tool for enterprise organizations",
            ideal_customer="CTOs, CEOs, VPs, and directors at companies and businesses",
            main_problem_solved="Enterprise technology solutions for teams",
        )

        _, confidence_low = classifier.classify_client(brief_low)
        _, confidence_high = classifier.classify_client(brief_high)

        # Higher keyword density should yield higher confidence
        assert confidence_high > confidence_low

    def test_classify_mixed_keywords(self):
        """Test classification when brief contains keywords from multiple types"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Hybrid Business",
            business_description="SaaS platform for coaches providing consulting services",
            ideal_customer="Professionals and businesses needing coaching software",
            main_problem_solved="Technology solutions for coaching consultants",
        )

        client_type, confidence = classifier.classify_client(brief)

        # Should pick the type with highest score (likely B2B_SAAS or COACH_CONSULTANT)
        assert client_type in [ClientType.B2B_SAAS, ClientType.COACH_CONSULTANT]
        assert confidence > 0.15


class TestGetClassificationReasoning:
    """Test get_classification_reasoning method"""

    def test_reasoning_for_b2b_saas(self):
        """Test reasoning generation for B2B SaaS"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="TechCo",
            business_description="SaaS platform for enterprise teams"
            + " x" * 100,  # Long description
            ideal_customer="CTOs at companies" + " y" * 100,  # Long customer description
            main_problem_solved="Technology solutions",
        )

        reasoning = classifier.get_classification_reasoning(brief, ClientType.B2B_SAAS, 0.85)

        assert "B2B Saas" in reasoning
        assert "85" in reasoning  # Confidence percentage
        assert "Business:" in reasoning
        assert "Customer:" in reasoning
        assert "SaaS platform" in reasoning[:200]  # Should include truncated description

    def test_reasoning_for_unknown(self):
        """Test reasoning generation for UNKNOWN type"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Mystery Co",
            business_description="Various services",
            ideal_customer="People",
            main_problem_solved="General problems",
        )

        reasoning = classifier.get_classification_reasoning(brief, ClientType.UNKNOWN, 0.05)

        assert "Unknown" in reasoning
        assert "uncertain" in reasoning.lower()
        assert "default safe template" in reasoning.lower()

    def test_reasoning_includes_confidence(self):
        """Test that reasoning includes confidence score"""
        classifier = ClientClassifier()
        brief = ClientBrief(
            company_name="Agency Co",
            business_description="Marketing agency",
            ideal_customer="Brands",
            main_problem_solved="Creative campaigns",
        )

        reasoning = classifier.get_classification_reasoning(brief, ClientType.AGENCY, 0.67)

        # Should show confidence as percentage (67%)
        assert "67" in reasoning or "67.0" in reasoning

    def test_reasoning_truncates_long_descriptions(self):
        """Test that reasoning truncates very long descriptions"""
        classifier = ClientClassifier()
        long_desc = "A" * 200  # Very long description
        brief = ClientBrief(
            company_name="Test Co",
            business_description=long_desc,
            ideal_customer="B" * 200,
            main_problem_solved="Test problem",
        )

        reasoning = classifier.get_classification_reasoning(brief, ClientType.B2B_SAAS, 0.75)

        # Should truncate to 100 chars + "..."
        assert "Business:" in reasoning
        assert "..." in reasoning
        # Full 200-char string shouldn't appear
        assert long_desc not in reasoning

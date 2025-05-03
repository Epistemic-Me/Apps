"""Research Agent for providing scientific information about health and longevity."""

from typing import Dict, Any, List, Optional
from bio_age_coach.agents.base_agent import Agent
from bio_age_coach.router.observation_context import ObservationContext

class ResearchAgent(Agent):
    """Agent for providing scientific information and research about health, longevity, and biological age."""
    
    def __init__(self, name: str, description: str, api_key: str, mcp_client):
        """Initialize the Research agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent's capabilities
            api_key: OpenAI API key
            mcp_client: MCP client for server communication
        """
        super().__init__(
            name=name,
            description=description,
            api_key=api_key,
            mcp_client=mcp_client
        )
    
    def _initialize_capabilities(self) -> None:
        """Initialize the capabilities of this agent."""
        self.capabilities = [
            "Provide scientific information about health and longevity",
            "Explain biological age concepts",
            "Summarize research studies",
            "Explain biomarkers and health metrics",
            "Provide evidence-based health recommendations",
            "Answer questions about aging science",
            "Explain health optimization strategies"
        ]
    
    def _initialize_servers(self) -> None:
        """Initialize server types this agent will communicate with."""
        self.server_types = {"research", "knowledge_base"}
        
    def _initialize_domain_examples(self) -> None:
        """Initialize examples of queries this agent can handle."""
        self.domain_examples = [
            "What is biological age?",
            "How is biological age calculated?",
            "What research exists on reducing biological age?",
            "Explain the science behind telomeres and aging",
            "What are the most important biomarkers for longevity?",
            "How does sleep affect aging?",
            "What does research say about intermittent fasting?",
            "Explain the role of NAD+ in aging",
            "What are the latest studies on exercise and longevity?",
            "How does stress impact biological age?",
            "What's the science behind the Mediterranean diet and longevity?",
            "Explain epigenetic clocks",
            "What are blue zones and why do people live longer there?",
            "How does inflammation affect aging?",
            "What research exists on supplements for longevity?"
        ]
        
    def _initialize_supported_data_types(self) -> None:
        """Initialize data types this agent can process."""
        self.supported_data_types = {"research"}
    
    async def can_handle(self, query: str, context: Dict[str, Any]) -> float:
        """Determine if this agent can handle the query.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            float: Confidence score between 0 and 1
        """
        # Check for research-related keywords
        research_keywords = [
            "research", "study", "studies", "science", "scientific", 
            "evidence", "journal", "publication", "paper", "experiment",
            "clinical trial", "meta-analysis", "review", "literature",
            "mechanism", "pathway", "biology", "cellular", "molecular",
            "explain how", "why does", "what causes", "theory", "hypothesis"
        ]
        
        # Check for health and longevity keywords
        health_keywords = [
            "longevity", "aging", "lifespan", "healthspan", "biological age",
            "biomarker", "telomere", "epigenetic", "methylation", "senescence",
            "inflammation", "oxidative stress", "mitochondria", "autophagy",
            "nad+", "sirtuins", "mtor", "ampk", "hormesis", "blue zones"
        ]
        
        # Calculate confidence based on keyword matches
        query_lower = query.lower()
        
        research_matches = sum(1 for keyword in research_keywords if keyword in query_lower)
        health_matches = sum(1 for keyword in health_keywords if keyword in query_lower)
        
        # Higher confidence if both research and health keywords are present
        if research_matches > 0 and health_matches > 0:
            return 0.9
        elif health_matches > 1:
            return 0.8
        elif research_matches > 0 or health_matches > 0:
            return 0.7
            
        # Check if query is asking for an explanation
        if query_lower.startswith("what is") or query_lower.startswith("how does") or query_lower.startswith("explain"):
            return 0.6
            
        return 0.3
    
    async def process(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process the query and return a response.
        
        Args:
            query: User query
            context: Conversation context
            
        Returns:
            Dict[str, Any]: Response
        """
        try:
            # Categorize the query
            query_lower = query.lower()
            
            # Determine the research topic
            if "biological age" in query_lower or "bio age" in query_lower:
                return await self._process_bio_age_query(query)
            elif "sleep" in query_lower:
                return await self._process_sleep_query(query)
            elif "exercise" in query_lower or "physical activity" in query_lower:
                return await self._process_exercise_query(query)
            elif "diet" in query_lower or "nutrition" in query_lower or "food" in query_lower:
                return await self._process_diet_query(query)
            elif "stress" in query_lower:
                return await self._process_stress_query(query)
            elif "supplement" in query_lower:
                return await self._process_supplement_query(query)
            else:
                return await self._process_general_query(query)
                
        except Exception as e:
            return {
                "response": "I encountered an error while researching this topic.",
                "insights": [],
                "references": [],
                "error": str(e)
            }
    
    async def _process_bio_age_query(self, query: str) -> Dict[str, Any]:
        """Process biological age query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "biological_age"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for biological age queries
        if "what is" in query.lower():
            return {
                "response": "Biological age refers to how old your body appears to be based on various biomarkers and physiological measurements, rather than the number of years you've been alive (chronological age). It's a measure of your body's functional capacity and health status.",
                "insights": [
                    "Biological age can be higher or lower than chronological age depending on lifestyle, genetics, and environmental factors.",
                    "Multiple methods exist to calculate biological age, including telomere length, epigenetic clocks, and composite biomarker algorithms.",
                    "Research shows that biological age is often a better predictor of mortality and disease risk than chronological age.",
                    "Lifestyle interventions can reduce biological age, even when chronological age continues to increase."
                ],
                "references": [
                    {"title": "DNA methylation age of human tissues and cell types", "authors": "Horvath S", "journal": "Genome Biology", "year": 2013, "doi": "10.1186/gb-2013-14-10-r115"},
                    {"title": "An epigenetic biomarker of aging for lifespan and healthspan", "authors": "Lu AT, et al.", "journal": "Aging", "year": 2019, "doi": "10.18632/aging.101684"},
                    {"title": "Quantitative Integration of Genetic and Non-genetic Determinants of Aging", "authors": "Belsky DW, et al.", "journal": "Current Opinion in Psychology", "year": 2019, "doi": "10.1016/j.copsyc.2018.11.010"}
                ],
                "error": None
            }
        elif "calculate" in query.lower() or "measure" in query.lower():
            return {
                "response": "Biological age can be calculated using several different methods, each with its own strengths and limitations. The most scientifically validated approaches include epigenetic clocks, which measure DNA methylation patterns, and biomarker composites, which analyze multiple blood biomarkers.",
                "insights": [
                    "Epigenetic clocks (like Horvath's clock) measure DNA methylation patterns at specific CpG sites to determine biological age.",
                    "Blood biomarker approaches (like PhenoAge and GlycanAge) use combinations of standard clinical markers to estimate biological age.",
                    "Telomere length measurement provides another estimate of biological age, though it's less precise than newer methods.",
                    "Functional assessments like grip strength, walking speed, and cognitive tests can contribute to biological age calculations.",
                    "Consumer tests typically use simplified versions of research methods, often combining blood biomarkers with questionnaire data."
                ],
                "references": [
                    {"title": "DNA methylation age of human tissues and cell types", "authors": "Horvath S", "journal": "Genome Biology", "year": 2013, "doi": "10.1186/gb-2013-14-10-r115"},
                    {"title": "An epigenetic biomarker of aging for lifespan and healthspan", "authors": "Lu AT, et al.", "journal": "Aging", "year": 2019, "doi": "10.18632/aging.101684"},
                    {"title": "Phenotypic Age: A novel signature of mortality and morbidity risk", "authors": "Levine ME, et al.", "journal": "Aging", "year": 2018, "doi": "10.18632/aging.101414"}
                ],
                "error": None
            }
        else:
            return {
                "response": "Biological age is a measure of how well or poorly your body is functioning relative to your chronological age. It's determined by analyzing various biomarkers and physiological measurements that change with age.",
                "insights": [
                    "Biological age can differ significantly from chronological age based on genetics, lifestyle, and environmental factors.",
                    "Research shows that biological age is often a better predictor of health outcomes and mortality risk than chronological age.",
                    "Factors that can accelerate biological aging include chronic stress, poor sleep, sedentary lifestyle, poor nutrition, and environmental toxins.",
                    "Interventions like regular exercise, healthy diet, quality sleep, and stress management can help reduce biological age."
                ],
                "references": [
                    {"title": "DNA methylation age of human tissues and cell types", "authors": "Horvath S", "journal": "Genome Biology", "year": 2013, "doi": "10.1186/gb-2013-14-10-r115"},
                    {"title": "Quantitative Integration of Genetic and Non-genetic Determinants of Aging", "authors": "Belsky DW, et al.", "journal": "Current Opinion in Psychology", "year": 2019, "doi": "10.1016/j.copsyc.2018.11.010"}
                ],
                "error": None
            }
    
    async def _process_sleep_query(self, query: str) -> Dict[str, Any]:
        """Process sleep-related query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "sleep"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for sleep queries
        return {
            "response": "Research consistently shows that sleep quality and duration are critical factors in the aging process and biological age. Both insufficient sleep (less than 7 hours) and excessive sleep (more than 9 hours) are associated with accelerated aging and increased mortality risk.",
            "insights": [
                "Sleep deprivation increases oxidative stress and inflammation, two key drivers of biological aging.",
                "During deep sleep, the glymphatic system clears waste products from the brain, including beta-amyloid associated with Alzheimer's disease.",
                "Poor sleep quality is associated with telomere shortening, a marker of cellular aging.",
                "Sleep fragmentation (frequent awakenings) has been linked to increased biological age independent of sleep duration.",
                "Consistent sleep schedules help maintain circadian rhythms, which regulate numerous age-related biological processes."
            ],
            "references": [
                {"title": "Sleep duration and telomere length in children", "authors": "James S, et al.", "journal": "Journal of Pediatrics", "year": 2017, "doi": "10.1016/j.jpeds.2017.06.055"},
                {"title": "Sleep disturbances and inflammatory biomarkers: The Multi-Ethnic Study of Atherosclerosis", "authors": "Nakamura K, et al.", "journal": "Sleep Medicine", "year": 2019, "doi": "10.1016/j.sleep.2019.01.002"},
                {"title": "Sleep and Human Aging", "authors": "Mander BA, et al.", "journal": "Neuron", "year": 2017, "doi": "10.1016/j.neuron.2017.02.004"}
            ],
            "error": None
        }
    
    async def _process_exercise_query(self, query: str) -> Dict[str, Any]:
        """Process exercise-related query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "exercise"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for exercise queries
        return {
            "response": "Regular physical activity is one of the most robust interventions for reducing biological age and extending healthspan. Research shows that both aerobic exercise and resistance training have significant anti-aging effects at the cellular and systemic levels.",
            "insights": [
                "Exercise increases mitochondrial biogenesis and function, improving cellular energy production and reducing oxidative stress.",
                "Regular physical activity has been shown to lengthen telomeres or slow their shortening rate, a key marker of cellular aging.",
                "Resistance training helps preserve muscle mass and strength, which naturally decline with age (sarcopenia).",
                "High-intensity interval training (HIIT) appears particularly effective at improving mitochondrial function in older adults.",
                "Even modest increases in physical activity, such as walking 7,000-10,000 steps daily, are associated with reduced biological age."
            ],
            "references": [
                {"title": "Enhanced Protein Translation Underlies Improved Metabolic and Physical Adaptations to Different Exercise Training Modes in Young and Old Humans", "authors": "Robinson MM, et al.", "journal": "Cell Metabolism", "year": 2017, "doi": "10.1016/j.cmet.2017.02.009"},
                {"title": "Physical activity and telomere length: Impact of aging and potential mechanisms of action", "authors": "Arsenis NC, et al.", "journal": "Oncotarget", "year": 2017, "doi": "10.18632/oncotarget.16726"},
                {"title": "Exercise attenuates the major hallmarks of aging", "authors": "Garatachea N, et al.", "journal": "Rejuvenation Research", "year": 2015, "doi": "10.1089/rej.2014.1623"}
            ],
            "error": None
        }
    
    async def _process_diet_query(self, query: str) -> Dict[str, Any]:
        """Process diet-related query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "nutrition"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for diet queries
        return {
            "response": "Dietary patterns have significant impacts on biological aging processes. Research consistently shows that Mediterranean, DASH, and plant-rich diets are associated with reduced biological age and lower risk of age-related diseases. Caloric restriction and intermittent fasting also show promising anti-aging effects.",
            "insights": [
                "Plant-rich diets provide polyphenols and antioxidants that combat oxidative stress and inflammation, key drivers of aging.",
                "Caloric restriction without malnutrition activates longevity pathways including sirtuins and AMPK while inhibiting mTOR.",
                "Intermittent fasting induces autophagy, a cellular cleaning process that removes damaged components and may slow aging.",
                "Excessive consumption of ultra-processed foods, refined carbohydrates, and sugar accelerates biological aging.",
                "Adequate protein intake (1.0-1.5g/kg/day) becomes increasingly important with age to prevent sarcopenia and maintain immune function."
            ],
            "references": [
                {"title": "Mediterranean Diet and Telomere Length in Nurses' Health Study: Population Based Cohort Study", "authors": "Crous-Bou M, et al.", "journal": "BMJ", "year": 2014, "doi": "10.1136/bmj.g6674"},
                {"title": "Caloric restriction improves health and survival of rhesus monkeys", "authors": "Colman RJ, et al.", "journal": "Nature Communications", "year": 2014, "doi": "10.1038/ncomms4557"},
                {"title": "Impact of Intermittent Fasting on Health and Disease Processes", "authors": "Mattson MP, et al.", "journal": "Ageing Research Reviews", "year": 2017, "doi": "10.1016/j.arr.2016.10.005"}
            ],
            "error": None
        }
    
    async def _process_stress_query(self, query: str) -> Dict[str, Any]:
        """Process stress-related query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "stress"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for stress queries
        return {
            "response": "Chronic psychological stress has been shown to accelerate biological aging through multiple pathways. Research demonstrates that prolonged stress exposure increases oxidative stress, inflammation, and shortens telomeres, all of which contribute to faster aging.",
            "insights": [
                "Chronic stress increases cortisol levels, which can damage telomeres and accelerate cellular aging.",
                "Stress-induced inflammation activates NF-κB signaling, a key regulator of aging-related gene expression.",
                "Psychological stress has been linked to decreased telomerase activity, the enzyme that maintains telomere length.",
                "Mindfulness meditation, yoga, and other stress-reduction techniques have been shown to reduce biological age markers.",
                "The relationship between stress and aging appears bidirectional - stress accelerates aging, and aging increases vulnerability to stress."
            ],
            "references": [
                {"title": "Accelerated telomere shortening in response to life stress", "authors": "Epel ES, et al.", "journal": "Proceedings of the National Academy of Sciences", "year": 2004, "doi": "10.1073/pnas.0407162101"},
                {"title": "Stress, Inflammation, and Aging", "authors": "Franceschi C, et al.", "journal": "Annual Review of Immunology", "year": 2018, "doi": "10.1146/annurev-immunol-042617-053236"},
                {"title": "Mindfulness meditation and improvement in sleep quality and daytime impairment among older adults with sleep disturbances", "authors": "Black DS, et al.", "journal": "JAMA Internal Medicine", "year": 2015, "doi": "10.1001/jamainternmed.2014.8081"}
            ],
            "error": None
        }
    
    async def _process_supplement_query(self, query: str) -> Dict[str, Any]:
        """Process supplement-related query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "supplements"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for supplement queries
        return {
            "response": "The research on supplements for longevity and biological age reduction shows mixed results. While some compounds show promise in laboratory and animal studies, human clinical evidence for most supplements remains limited. The most researched compounds include NAD+ precursors (NMN, NR), resveratrol, spermidine, and certain antioxidants.",
            "insights": [
                "NAD+ precursors (nicotinamide riboside, nicotinamide mononucleotide) may improve mitochondrial function and cellular energy production.",
                "Resveratrol activates sirtuins, proteins involved in cellular health and longevity, though human studies show inconsistent results.",
                "Spermidine induces autophagy, a cellular cleaning process that may slow aging, with some human epidemiological evidence supporting its benefits.",
                "Vitamin D deficiency is associated with accelerated aging; supplementation may be beneficial for those with low levels.",
                "Most supplements lack robust human clinical trials demonstrating anti-aging effects; lifestyle interventions currently have stronger evidence."
            ],
            "references": [
                {"title": "Chronic nicotinamide riboside supplementation is well-tolerated and elevates NAD+ in healthy middle-aged and older adults", "authors": "Martens CR, et al.", "journal": "Nature Communications", "year": 2018, "doi": "10.1038/s41467-018-03421-7"},
                {"title": "Effects of Resveratrol on Memory Performance, Hippocampal Functional Connectivity, and Glucose Metabolism in Healthy Older Adults", "authors": "Witte AV, et al.", "journal": "Journal of Neuroscience", "year": 2014, "doi": "10.1523/JNEUROSCI.0385-14.2014"},
                {"title": "Spermidine in health and disease", "authors": "Madeo F, et al.", "journal": "Science", "year": 2018, "doi": "10.1126/science.aan2788"}
            ],
            "error": None
        }
    
    async def _process_general_query(self, query: str) -> Dict[str, Any]:
        """Process general longevity query.
        
        Args:
            query: User query
            
        Returns:
            Dict[str, Any]: Response
        """
        # Try to fetch information from knowledge base
        try:
            response = await self.mcp_client.send_request(
                "knowledge_base",
                {
                    "type": "search",
                    "query": query,
                    "topic": "longevity"
                }
            )
            
            if "error" not in response and "results" in response:
                results = response["results"]
                if results:
                    return self._format_knowledge_response(results, query)
        except Exception:
            # Fall back to hardcoded response if knowledge base fails
            pass
        
        # Hardcoded response for general longevity queries
        return {
            "response": "Longevity research has identified several key hallmarks of aging: genomic instability, telomere attrition, epigenetic alterations, loss of proteostasis, deregulated nutrient sensing, mitochondrial dysfunction, cellular senescence, stem cell exhaustion, and altered intercellular communication. Interventions targeting these pathways show promise for extending healthspan and potentially lifespan.",
            "insights": [
                "The most robust interventions for slowing biological aging include regular physical activity, plant-rich diet, adequate sleep, stress management, and social connection.",
                "Caloric restriction without malnutrition consistently extends lifespan in model organisms, though long-term human studies are limited.",
                "Emerging pharmaceutical approaches include senolytics (drugs that clear senescent cells) and mTOR inhibitors like rapamycin.",
                "Biological age can be measured through various biomarkers including DNA methylation patterns, which form the basis of 'epigenetic clocks'.",
                "Genetic factors account for approximately 25% of longevity variation, with lifestyle and environmental factors playing larger roles."
            ],
            "references": [
                {"title": "The Hallmarks of Aging", "authors": "López-Otín C, et al.", "journal": "Cell", "year": 2013, "doi": "10.1016/j.cell.2013.05.039"},
                {"title": "Interventions to Slow Aging in Humans: Are We Ready?", "authors": "Longo VD, et al.", "journal": "Aging Cell", "year": 2015, "doi": "10.1111/acel.12338"},
                {"title": "Aging, Cellular Senescence, and Cancer", "authors": "Campisi J", "journal": "Annual Review of Physiology", "year": 2013, "doi": "10.1146/annurev-physiol-030212-183653"}
            ],
            "error": None
        }
    
    def _format_knowledge_response(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Format knowledge base results into a response.
        
        Args:
            results: Knowledge base results
            query: Original query
            
        Returns:
            Dict[str, Any]: Formatted response
        """
        # Extract main response from first result
        main_response = results[0].get("content", "")
        
        # Extract insights from all results
        insights = []
        for result in results:
            if "key_points" in result:
                insights.extend(result["key_points"])
        
        # Limit insights to top 5
        insights = insights[:5]
        
        # Extract references
        references = []
        for result in results:
            if "reference" in result:
                ref = result["reference"]
                if isinstance(ref, dict):
                    references.append(ref)
                elif isinstance(ref, list):
                    references.extend(ref)
        
        # Limit references to top 3
        references = references[:3]
        
        return {
            "response": main_response,
            "insights": insights,
            "references": references,
            "error": None
        }
    
    async def create_observation_context(self, data_type: str, user_id: Optional[str] = None) -> Optional[ObservationContext]:
        """Create an observation context for the given data type.
        
        Args:
            data_type: Type of data to create context for
            user_id: Optional user ID
            
        Returns:
            Optional[ObservationContext]: Observation context or None if not supported
        """
        # Research agent creates a generic observation context for research-related queries
        if data_type == "research":
            return ObservationContext(agent_name=self.name, data_type=data_type, user_id=user_id)
        
        # Research agent doesn't process other types of user data
        return None 